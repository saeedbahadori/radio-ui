from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# serve index.html
app.mount("/", StaticFiles(directory=".", html=True), name="ui")

# health check
@app.get("/health")
def health():
    return {"status": "ok"}
