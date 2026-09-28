let currentCategory = "all";
let deleteId = null;
const grid = document.getElementById("grid");
const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " Б";
  if (bytes < 1024**2) return (bytes/1024).toFixed(1) + " КБ";
  if (bytes < 1024**3) return (bytes/1024**2).toFixed(1) + " МБ";
  return (bytes/1024**3).toFixed(1) + " ГБ";
}
function icon(ext) {
  const map = {pdf:"▤",doc:"W",docx:"W",xls:"X",xlsx:"X",ppt:"P",pptx:"P",
               jpg:"▧",jpeg:"▧",png:"▧",gif:"▧",webp:"▧",zip:"⌘",rar:"⌘",txt:"T",csv:"C"};
  return map[ext] || "•";
}
function categoryFor(ext) {
  if (ext === "pdf") return "PDF";
  if (["doc","docx","odt","rtf","txt"].includes(ext)) return "Word";
  if (["xls","xlsx","ods","csv"].includes(ext)) return "Excel";
  if (["ppt","pptx","odp"].includes(ext)) return "PowerPoint";
  if (["jpg","jpeg","png","gif","webp"].includes(ext)) return "IMAGE";
  if (["zip","rar","7z"].includes(ext)) return "ZIP";
  return ext.toUpperCase();
}
function dateText(iso) {
  return new Date(iso).toLocaleString("kk-KZ", {day:"2-digit", month:"2-digit", year:"numeric", hour:"2-digit", minute:"2-digit"});
}
function toast(msg, error=false) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast show" + (error ? " error" : "");
  setTimeout(() => t.className = "toast", 2800);
}
async function loadStats() {
  const r = await fetch("/api/stats");
  const s = await r.json();
  for (const k of ["total","pdf","documents","images"]) document.getElementById(k).textContent = s[k];
}
async function loadFiles() {
  const q = encodeURIComponent(document.getElementById("search").value);
  const sort = document.getElementById("sort").value;
  const r = await fetch(`/api/files?q=${q}&category=${currentCategory}&sort=${sort}`);
  const files = await r.json();
  document.getElementById("count").textContent = files.length + " файл";
  if (!files.length) {
    grid.innerHTML = `<div class="empty"><div>🧪</div><h3>Мұнда әзірге бос</h3><p>Химия бойынша бірінші материалды жүктеңіз</p></div>`;
    return;
  }
  grid.innerHTML = files.map(f => `
    <article class="file-card">
      <a class="file-main" href="${f.url}" target="_blank" rel="noopener">
        <div class="file-icon ${f.extension}">${icon(f.extension)}</div>
        <div class="file-info"><h3 title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</h3>
        <div class="meta"><span>${categoryFor(f.extension)}</span><span>${formatSize(f.size)}</span></div>
        <small>${dateText(f.uploaded_at)}</small></div>
      </a>
      <div class="card-actions">
        <a class="download" href="${f.download_url}">↓ Жүктеу</a>
        <button class="trash" onclick="askDelete(${f.id}, '${escapeJs(f.name)}')" aria-label="Өшіру">⌫</button>
      </div>
    </article>`).join("");
}
function escapeHtml(s) { return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
function escapeJs(s) { return s.replace(/\\/g,"\\\\").replace(/'/g,"\\'").replace(/\n/g," "); }

function openUpload() { fileInput.click(); }
function closeModal() { document.getElementById("modal").classList.remove("open"); deleteId = null; }
function askDelete(id, name) {
  deleteId = id;
  document.getElementById("deleteName").textContent = name;
  document.getElementById("modal").classList.add("open");
}
document.getElementById("confirmDelete").onclick = async () => {
  const r = await fetch(`/api/files/${deleteId}`, {method:"DELETE"});
  if (r.ok) { closeModal(); toast("Файл өшірілді"); await loadFiles(); await loadStats(); }
  else toast("Өшіру кезінде қате болды", true);
};

async function upload(file) {
  if (!file) return;
  const form = new FormData(); form.append("file", file);
  document.getElementById("progressWrap").classList.add("show");
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/files");
  xhr.upload.onprogress = e => {
    if (e.lengthComputable) document.getElementById("progress").style.width = (e.loaded/e.total*100)+"%";
  };
  xhr.onload = async () => {
    document.getElementById("progressWrap").classList.remove("show");
    document.getElementById("progress").style.width = "0";
    if (xhr.status >= 200 && xhr.status < 300) { toast("Файл сәтті жүктелді ✨"); await loadFiles(); await loadStats(); }
    else { let msg="Файлды жүктеу кезінде қате болды"; try { msg=JSON.parse(xhr.responseText).detail || msg; } catch{} toast(msg,true); }
  };
  xhr.onerror = () => { document.getElementById("progressWrap").classList.remove("show"); toast("Желі қатесі",true); };
  xhr.send(form);
}
fileInput.onchange = () => upload(fileInput.files[0]);
dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("drag"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag"));
dropzone.addEventListener("drop", e => { e.preventDefault(); dropzone.classList.remove("drag"); upload(e.dataTransfer.files[0]); });

document.querySelectorAll(".filter").forEach(btn => btn.onclick = () => {
  document.querySelectorAll(".filter").forEach(b => b.classList.remove("active"));
  btn.classList.add("active"); currentCategory = btn.dataset.cat; loadFiles();
});
document.getElementById("search").oninput = () => loadFiles();
document.getElementById("sort").onchange = () => loadFiles();
document.getElementById("modal").onclick = e => { if(e.target.id==="modal") closeModal(); };

loadFiles(); loadStats();
