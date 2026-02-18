import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# ===============================
# OpenAI
# ===============================
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# حافظه ساده سشن‌ها
sessions = {}

# ===============================
# MODELS
# ===============================

class ChatRequest(BaseModel):
    message: str
    session_id: str


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
# RADIO PRODUCER (STEP BY STEP)
# ===============================
@app.post("/api/chat")
def chat(req: ChatRequest):

    session_id = req.session_id
    user_message = req.message.strip()

    # ساخت سشن جدید
    if session_id not in sessions:
        sessions[session_id] = {"step": "program_name"}
        return {"reply": "🎙️ سلام! اسم برنامه رادیویی چی باشه؟"}

    state = sessions[session_id]

    # -------- STEP 1 : NAME --------
    if state["step"] == "program_name":
        state["program_name"] = user_message
        state["step"] = "topic"
        return {"reply": "موضوع برنامه درباره چی باشه؟"}

    # -------- STEP 2 : TOPIC --------
    elif state["step"] == "topic":
        state["topic"] = user_message
        state["step"] = "tone"
        return {"reply": "چه لحنی می‌خوای؟ (صمیمی، رسمی، انگیزشی، داستانی)"}

    # -------- STEP 3 : TONE --------
    elif state["step"] == "tone":
        state["tone"] = user_message
        state["step"] = "duration"
        return {"reply": "مدت زمان برنامه چند دقیقه باشه؟"}

    # -------- STEP 4 : DURATION --------
    elif state["step"] == "duration":
        state["duration"] = user_message
        state["step"] = "confirm"

        summary = f"""
نام برنامه: {state['program_name']}
موضوع: {state['topic']}
لحن: {state['tone']}
مدت: {state['duration']} دقیقه
"""

        return {
            "reply": f"👌 مشخصات برنامه:\n{summary}\nاگر تایید می‌کنی بنویس «بله»."
        }

    # -------- STEP 5 : GENERATE SCRIPT --------
    elif state["step"] == "confirm":

        if "بله" not in user_message:
            state["step"] = "program_name"
            return {"reply": "باشه، از اول شروع کنیم. اسم برنامه چیه؟"}

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
تو نویسنده حرفه‌ای رادیو هستی.

بر اساس اطلاعات زیر یک متن کامل برنامه رادیویی بنویس:

نام برنامه: {state['program_name']}
موضوع: {state['topic']}
لحن: {state['tone']}
مدت زمان: {state['duration']} دقیقه

متن باید آماده اجرا باشد.
"""
                }
            ],
            temperature=0.9,
            max_tokens=700
        )

        script = response.choices[0].message.content

        state["step"] = "done"

        return {"reply": script}

    # -------- RESET --------
    else:
        sessions.pop(session_id, None)
        return {"reply": "برنامه تمام شد 🎧 برای برنامه جدید اسم برنامه را بنویس."}


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
