import os
import uuid
import re
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

sessions = {}

# ===============================
# MODEL
# ===============================

class ChatRequest(BaseModel):
    message: str
    session_id: str
    voice: str | None = None


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
# MAIN FLOW
# ===============================

@app.post("/api/chat")
def chat(req: ChatRequest):

    session_id = req.session_id
    user_message = req.message.strip()

    if session_id not in sessions:
        sessions[session_id] = {"step": "program_name"}
        return {"reply": "🎙️ سلام! اسم برنامه رادیویی چی باشه؟"}

    state = sessions[session_id]

    if state["step"] == "program_name":
        state["program_name"] = user_message
        state["step"] = "topic"
        return {"reply": "موضوع برنامه درباره چی باشه؟"}

    elif state["step"] == "topic":
        state["topic"] = user_message
        state["step"] = "tone"
        return {"reply": "چه لحنی می‌خوای؟"}

    elif state["step"] == "tone":
        state["tone"] = user_message
        state["step"] = "duration"
        return {"reply": "مدت زمان برنامه چند دقیقه باشه؟"}

    elif state["step"] == "duration":
        state["duration"] = user_message
        state["step"] = "confirm"

        return {
            "reply": f"""
👌 مشخصات برنامه:

نام: {state['program_name']}
موضوع: {state['topic']}
لحن: {state['tone']}
مدت: {state['duration']} دقیقه

اگر تایید می‌کنی بنویس «بله».
"""
        }

    elif state["step"] == "confirm":

        if "بله" not in user_message:
            state["step"] = "program_name"
            return {"reply": "باشه از اول شروع کنیم. اسم برنامه چیه؟"}

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

فقط متن گوینده را بنویس.
هیچ توضیح صحنه یا پرانتز ننویس.
"""
                }
            ],
            temperature=0.9,
            max_tokens=900
        )

        script = response.choices[0].message.content

        state["final_script"] = script
        state["step"] = "voice_select"

        return {
            "reply": script + "\n\n🎧 با چه صدایی پخش شود؟"
        }

    elif state["step"] == "voice_select":

        if not req.voice:
            return {"reply": "لطفاً یکی از صداها را انتخاب کن."}

        text = state["final_script"]

        # پاکسازی قبل از TTS
        text = re.sub(r"\(.*?\)", "", text)
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\*.*?\*", "", text)
        text = re.sub(r"\n{2,}", "\n", text)
        text = text.strip()

        file_id = str(uuid.uuid4())
        file_path = os.path.join(AUDIO_DIR, f"{file_id}.mp3")

        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=req.voice,
            input=text
        ) as response:
            response.stream_to_file(file_path)

        sessions.pop(session_id, None)

        return {
            "reply": "🎧 فایل صوتی آماده شد.",
            "audio_url": f"/audio/{file_id}.mp3"
        }

    sessions.pop(session_id, None)
    return {"reply": "برنامه جدیدی شروع کنیم."}


@app.get("/audio/{filename}")
def get_audio(filename: str):
    path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "file not found"})
    return FileResponse(path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
