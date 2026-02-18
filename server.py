import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# ===============================
# OpenAI Client (Safe Init)
# ===============================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

# مسیر پروژه
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ===============================
# MODELS
# ===============================

class RadioRequest(BaseModel):
    topic: str


class ChatRequest(BaseModel):
    message: str


# ===============================
# ROUTES
# ===============================

# صفحه اصلی
@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# تست سلامت سرور
@app.get("/ping")
def ping():
    return {"status": "ok"}


# وضعیت رادیو
@app.get("/api/status")
def status():
    return JSONResponse({"radio": "online"})


# -------------------------------
# تولید متن برنامه رادیویی
# -------------------------------
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


# -------------------------------
# CHAT AI (Connected to OpenAI)
# -------------------------------
@app.post("/api/chat")
def chat(req: ChatRequest):

    if client is None:
        return {
            "reply": "⚠️ هوش مصنوعی هنوز فعال نشده (OPENAI_API_KEY تنظیم نشده)."
        }

    user_message = req.message.strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
تو یک گوینده حرفه‌ای رادیویی فارسی هستی.
پاسخ‌ها کوتاه، گرم، شنیداری و مناسب اجرای رادیویی باشند.
لحن الهام‌بخش و صمیمی داشته باش.
حداکثر 4 جمله پاسخ بده.
"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.8,
        max_tokens=200
    )

    reply = response.choices[0].message.content

    return {"reply": reply}


# ===============================
# SERVER START (Railway)
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
