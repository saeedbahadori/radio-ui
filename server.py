import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# serve index.html
@app.get("/")
def read_index():
    return FileResponse("index.html")

# serve static files if needed
app.mount("/", StaticFiles(directory=".", html=True), name="static")
