import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

# مسیر پوشه پروژه
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------- ROUTES ----------

# صفحه اصلی (UI)
@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# تست زنده بودن سرور
@app.get("/ping")
def ping():
    return {"status": "ok"}


# وضعیت رادیو (API واقعی برای UI)
@app.get("/api/status")
def status():
    return JSONResponse({"radio": "online"})


# ---------- SERVER START ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "server:app",   # مهم: فرمت استاندارد ASGI
        host="0.0.0.0",
        port=port,
        reload=False
    )
