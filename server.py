import os
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))
