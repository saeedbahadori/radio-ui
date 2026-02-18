import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# ===============================
# OpenAI
# ===============================
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ===============================
# MODELS
# ===============================

class ChatRequest(BaseModel):
    message: str


# ===============================
# ROUTES
# ===============================

@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    return {"radio": "online"}


# ===============================
# RADIO BROADCAST (AI CHAT)
# ===============================
@app.post("/api/chat")
def chat(req: ChatRequest):

    user_message = req.message.strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
تو گوینده اولین رادیوی هوش مصنوعی جهان هستی.
پاسخ‌ها کوتاه، گرم، شنیداری و شبیه اجرای رادیویی باشند.
لحن صمیمی، الهام‌بخش و زنده داشته باش.
حداکثر 4 جمله بگو.
در پایان جمله‌ای شبیه امضای رادیویی اضافه کن.
"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.9,
        max_tokens=200
    )

    reply = response.choices[0].message.content

    return {"reply": reply}


# ===============================
# START SERVER
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
