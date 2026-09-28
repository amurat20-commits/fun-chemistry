# Fun Chemistry 🧪

Қазақ тіліндегі, Python/FastAPI негізіндегі көпқолданушы оқу файлдары қоймасы.

## Маңызды production ескертуі

Бұл жоба жергілікті режимде файлдарды `uploads/` қалтасына сақтайды. Бұл development үшін ыңғайлы, бірақ ephemeral контейнері бар хостингте production storage ретінде қолдануға болмайды.

Нақты public deployment үшін:
- PostgreSQL — persistent database;
- S3-compatible object storage — persistent file storage;
- HTTPS — хостинг платформасының domain/SSL қызметі;
- environment variables — барлық құпия параметрлер.

Қазіргі кодтың storage интерфейсі бөлек `app/storage.py` файлында орналасқан, сондықтан S3/R2/MinIO adapter-іне ауыстыруға ыңғайлы.

## 1. Орнату

Python 3.11+ ұсынылады.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
```

## 2. Environment

```bash
cp .env.example .env
```

Windows-та `.env` файлын қолмен жасаңыз.

Local development үшін SQLite әдепкі бойынша қолданылады.

## 3. Іске қосу

```bash
uvicorn app.main:app --reload
```

Браузерде:

`http://127.0.0.1:8000`

## 4. Production PostgreSQL

`DATABASE_URL` environment variable-іне PostgreSQL connection string беріңіз:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

Қосымша migration framework жоқ: startup кезінде SQLAlchemy кестені жасайды. Үлкен production жүйесінде Alembic migration қолдану ұсынылады.

## 5. Persistent файл сақтау

Production-та `LOCAL_UPLOAD_DIR`-ке сенбеңіз. Render/Railway/Fly.io сияқты ephemeral filesystem-і бар ортада container қайта іске қосылғанда файл жоғалуы мүмкін.

S3-compatible storage ретінде Cloudflare R2, AWS S3 немесе басқа object storage қолдануға болады. `app/storage.py` ішіндегі `save_upload()` және `delete_local()` функцияларын object-storage adapter-імен ауыстырып, database-та `storage_path` орнына object key/URL сақтаңыз.

Қажетті environment variables:

```text
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=...
S3_BUCKET=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_REGION=...
```

## 6. Public deployment

Кез келген Python ASGI hosting provider таңдаңыз.

Build/install command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Хостингте:
1. GitHub repository-ді қосыңыз.
2. PostgreSQL database provision жасаңыз.
3. Persistent object storage bucket жасаңыз.
4. `DATABASE_URL`, `SECRET_KEY` және storage credentials environment variables ретінде енгізіңіз.
5. HTTPS custom/platform domain қосыңыз.
6. Deployment аяқталған соң provider берген `https://...` URL арқылы сайтты ашыңыз.

## 7. Тексеру

1. Public HTTPS URL-ді телефоннан ашыңыз.
2. PDF немесе DOCX жүктеңіз.
3. Жүктеу аяқталғаннан кейін карточка автоматты пайда болады.
4. Басқа телефон/компьютерден сол URL-ді ашыңыз.
5. Файлдың көрінетінін тексеріңіз.
6. Файлды ашып/жүктеп көріңіз.
7. Екінші файл жүктеңіз.
8. Бір файлды өшіріңіз.
9. Бетті жаңартыңыз — өзгерістер database/storage ішінде сақталуы керек.

## Қауіпсіздік

- Original filename серверде path ретінде қолданылмайды.
- `Path(filename).name` арқылы basename алынады.
- Серверлік filename UUID арқылы жасалады.
- Allowed extension whitelist бар.
- Maximum upload size environment variable арқылы шектеледі.
- Secrets кодта сақталмайды.

## Әрі қарай production hardening

Public multi-user сервис болғандықтан, production алдында authentication/authorization, rate limiting, antivirus scanning, signed/private object-storage URLs, CSRF strategy және background cleanup jobs қосу керек.
