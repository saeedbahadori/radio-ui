import os
import uuid
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
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# حافظه سشن‌ها
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


@app.get("/api/status")
def status():
    return {"radio": "online"}


# ===============================
# RADIO FLOW
# ===============================

@app.post("/api/chat")
def chat(req: ChatRequest):

    session_id = req.session_id
    user_message = req.message.strip()

    if session_id not in sessions:
        sessions[session_id] = {"step": "program_name"}
        return {"reply": "🎙️ سلام! اسم برنامه رادیویی چی باشه؟"}

    state = sessions[session_id]

    # STEP 1 — PROGRAM NAME
    if state["step"] == "program_name":
        state["program_name"] = user_message
        state["step"] = "topic"
        return {"reply": "موضوع برنامه درباره چی باشه؟"}

    # STEP 2 — TOPIC
    elif state["step"] == "topic":
        state["topic"] = user_message
        state["step"] = "tone"
        return {"reply": "چه لحنی می‌خوای؟ (صمیمی، رسمی، انگیزشی، داستانی)"}

    # STEP 3 — TONE
    elif state["step"] == "tone":
        state["tone"] = user_message
        state["step"] = "duration"
        return {"reply": "مدت زمان برنامه چند دقیقه باشه؟"}

    # STEP 4 — DURATION
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

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"""
تو نویسنده حرفه‌ای رادیو هستی.

نام برنامه: {state['program_name']}
موضوع: {state['topic']}
لحن: {state['tone']}
مدت: {state['duration']} دقیقه

یک متن کامل، طبیعی و آماده اجرای رادیویی بنویس.
"""
                    }
                ],
                temperature=0.9,
                max_tokens=1000
            )

            script = response.choices[0].message.content

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"reply": f"خطا در تولید متن: {str(e)}"}
            )

        state["final_script"] = script
        state["step"] = "ready_for_audio"

        return {
            "reply": script + "\n\nاگر تایید نهایی است بنویس «تولید صدا»."
        }

    # STEP 6 — GENERATE AUDIO
    elif state["step"] == "ready_for_audio":

        if "تولید صدا" not in user_message:
            return {"reply": "برای دریافت فایل صوتی بنویس «تولید صدا»."}

        text = state["final_script"]
        file_id = str(uuid.uuid4())
        file_path = os.path.join(AUDIO_DIR, f"{file_id}.mp3")

        try:
            with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text
            ) as response:

                response.stream_to_file(file_path)

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"reply": f"خطا در تولید صدا: {str(e)}"}
            )

        sessions.pop(session_id, None)

        return {
            "reply": "🎧 فایل صوتی آماده شد.",
            "audio_url": f"/audio/{file_id}.mp3"
        }

    # RESET
    sessions.pop(session_id, None)
    return {"reply": "برنامه جدیدی شروع کنیم. اسم برنامه چیه؟"}


# ===============================
# AUDIO ROUTE
# ===============================

@app.get("/audio/{filename}")
def get_audio(filename: str):
    file_path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "file not found"})
    return FileResponse(file_path)


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
