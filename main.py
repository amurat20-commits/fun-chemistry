import os
import mimetypes
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .database import SessionLocal, init_db
from .models import FileRecord
from .storage import save_upload, delete_local

app = FastAPI(title="Fun Chemistry")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

ALLOWED_EXTENSIONS = {
    "pdf","doc","docx","xls","xlsx","ppt","pptx","txt","csv",
    "jpg","jpeg","png","gif","webp","zip","rar","7z",
    "odt","ods","odp","rtf","md","json","xml"
}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "100")) * 1024 * 1024

@app.on_event("startup")
def startup():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/files")
def list_files(q: str = "", category: str = "all", sort: str = "newest",
               db: Session = Depends(get_db)):
    query = db.query(FileRecord)
    if q.strip():
        query = query.filter(FileRecord.original_name.ilike(f"%{q.strip()}%"))

    image_ext = {"jpg","jpeg","png","gif","webp"}
    categories = {
        "pdf": {"pdf"},
        "word": {"doc","docx","odt","rtf"},
        "excel": {"xls","xlsx","ods","csv"},
        "powerpoint": {"ppt","pptx","odp"},
        "images": image_ext,
        "archives": {"zip","rar","7z"},
    }
    if category in categories:
        query = query.filter(FileRecord.extension.in_(categories[category]))

    if sort == "oldest":
        query = query.order_by(FileRecord.uploaded_at.asc())
    elif sort == "name":
        query = query.order_by(FileRecord.original_name.asc())
    elif sort == "size":
        query = query.order_by(FileRecord.size.asc())
    else:
        query = query.order_by(FileRecord.uploaded_at.desc())

    records = query.all()
    return [{
        "id": r.id,
        "name": r.original_name,
        "size": r.size,
        "extension": r.extension,
        "mime_type": r.mime_type,
        "uploaded_at": r.uploaded_at.isoformat(),
        "url": f"/api/files/{r.id}/open",
        "download_url": f"/api/files/{r.id}/download"
    } for r in records]

@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    records = db.query(FileRecord).all()
    return {
        "total": len(records),
        "pdf": sum(r.extension == "pdf" for r in records),
        "documents": sum(r.extension in {"doc","docx","odt","rtf","txt"} for r in records),
        "images": sum(r.extension in {"jpg","jpeg","png","gif","webp"} for r in records),
    }

@app.post("/api/files")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not Path(file.filename).name.strip():
        raise HTTPException(400, "Файлдың аты бос болмауы керек.")

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, "Бұл файл форматына рұқсат етілмеген.")

    data = await save_upload(file)
    if data["size"] > MAX_FILE_SIZE:
        delete_local(data["stored_name"])
        raise HTTPException(413, f"Файл өлшемі {MAX_FILE_SIZE // 1024 // 1024} MB-тан аспауы керек.")

    record = FileRecord(**data)
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "name": record.original_name,
        "message": "Файл сәтті жүктелді ✨"
    }

def get_record(file_id: int, db: Session):
    record = db.get(FileRecord, file_id)
    if not record:
        raise HTTPException(404, "Файл табылмады.")
    return record

@app.get("/api/files/{file_id}/open")
def open_file(file_id: int, db: Session = Depends(get_db)):
    record = get_record(file_id, db)
    path = Path(record.storage_path).resolve()
    if not path.exists():
        raise HTTPException(404, "Файл сақтау қоймасынан табылмады.")
    return FileResponse(path, media_type=record.mime_type or "application/octet-stream",
                        headers={"Content-Disposition": f'inline; filename="{quote(record.original_name)}"'})

@app.get("/api/files/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    record = get_record(file_id, db)
    path = Path(record.storage_path).resolve()
    if not path.exists():
        raise HTTPException(404, "Файл сақтау қоймасынан табылмады.")
    return FileResponse(path, media_type=record.mime_type or "application/octet-stream",
                        filename=record.original_name)

@app.delete("/api/files/{file_id}")
def remove_file(file_id: int, db: Session = Depends(get_db)):
    record = get_record(file_id, db)
    delete_local(record.stored_name)
    db.delete(record)
    db.commit()
    return {"message": "Файл өшірілді"}
