import os
import uuid
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
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

# اگر پوشه audio نبود بساز
os.makedirs(AUDIO_DIR, exist_ok=True)

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
# RADIO PRODUCER FLOW
# ===============================
@app.post("/api/chat")
def chat(req: ChatRequest):

    session_id = req.session_id
    user_message = req.message.strip()

    if session_id not in sessions:
        sessions[session_id] = {"step": "program_name"}
        return {"reply": "🎙️ سلام! اسم برنامه رادیویی چی باشه؟"}

    state = sessions[session_id]

    # STEP 1
    if state["step"] == "program_name":
        state["program_name"] = user_message
        state["step"] = "topic"
        return {"reply": "موضوع برنامه درباره چی باشه؟"}

    # STEP 2
    elif state["step"] == "topic":
        state["topic"] = user_message
        state["step"] = "tone"
        return {"reply": "چه لحنی می‌خوای؟ (صمیمی، رسمی، انگیزشی، داستانی)"}

    # STEP 3
    elif state["step"] == "tone":
        state["tone"] = user_message
        state["step"] = "duration"
        return {"reply": "مدت زمان برنامه چند دقیقه باشه؟"}

    # STEP 4
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

    # STEP 5 — GENERATE SCRIPT
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

نام برنامه: {state['program_name']}
موضوع: {state['topic']}
لحن: {state['tone']}
مدت: {state['duration']} دقیقه

یک متن کامل و آماده اجرای رادیویی بنویس.
"""
                }
            ],
            temperature=0.9,
            max_tokens=700
        )

        script = response.choices[0].message.content

        # متن نهایی داخل session ذخیره شود
        state["final_script"] = script
        state["step"] = "done"

        return {
            "reply": script + "\n\nاگر تایید نهایی است بنویس «تولید صدا»."
        }

    # STEP 6 — CREATE VOICE
    elif state["step"] == "done":

        if "تولید صدا" not in user_message:
            return {"reply": "برای دریافت فایل صوتی بنویس «تولید صدا»."}

        text = state["final_script"]

        file_id = str(uuid.uuid4())
        file_path = os.path.join(AUDIO_DIR, f"{file_id}.mp3")

        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
        )

        with open(file_path, "wb") as f:
            f.write(speech.read())

        sessions.pop(session_id, None)

        return {
            "reply": "🎧 فایل صوتی آماده شد.",
            "audio_url": f"/audio/{file_id}.mp3"
        }

    # RESET
    sessions.pop(session_id, None)
    return {"reply": "برنامه جدیدی شروع کنیم. اسم برنامه چیه؟"}


# ===============================
# AUDIO DOWNLOAD
# ===============================
@app.get("/audio/{filename}")
def get_audio(filename: str):
    return FileResponse(os.path.join(AUDIO_DIR, filename))


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
