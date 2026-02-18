import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()

# مسیر پوشه پروژه
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==================================================
# MODELS
# ==================================================

class RadioRequest(BaseModel):
    topic: str


class ChatRequest(BaseModel):
    message: str


# ==================================================
# ROUTES
# ==================================================

# صفحه اصلی (UI)
@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# تست زنده بودن سرور
@app.get("/ping")
def ping():
    return {"status": "ok"}


# وضعیت رادیو (برای UI)
@app.get("/api/status")
def status():
    return JSONResponse({"radio": "online"})


# --------------------------------------------------
# تولید متن برنامه رادیویی
# --------------------------------------------------
@app.post("/api/generate")
def generate_radio(req: RadioRequest):

    topic = req.topic.strip()

    script = f"""
🎙️ برنامه رادیویی هوش مصنوعی

موضوع امروز: {topic}

سلام به شنوندگان عزیز،
شما به اولین رادیوی هوش مصنوعی جهان گوش می‌دهید.

امروز درباره «{topic}» صحبت می‌کنیم؛
موضوعی که آینده را شکل می‌دهد و نگاه ما به جهان را تغییر می‌دهد.

با ما همراه باشید...
"""

    return {"script": script}


# --------------------------------------------------
# CHAT API (چت داخل صفحه اصلی)
# --------------------------------------------------
@app.post("/api/chat")
def chat(req: ChatRequest):

    user_message = req.message.strip()

    reply = f"""
🎙️ رادیو هوش مصنوعی:

درباره «{user_message}» صحبت جالبی مطرح کردی.

اگر بخوایم رادیویی نگاه کنیم،
این موضوع جاییه که تکنولوژی، احساس و داستان به هم می‌رسن.

با ما همراه باش...
"""

    return {"reply": reply}


# ==================================================
# SERVER START (Railway Compatible)
# ==================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
