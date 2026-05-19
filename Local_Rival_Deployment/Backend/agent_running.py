from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
from AI_Agent_RIval import run_agent

app = FastAPI()

templates = Jinja2Templates(directory="templates")


# =========================
# UI PAGE
# =========================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# =========================
# CODE INPUT
# =========================
@app.post("/run-agent/code")
async def run_code(code: str = Form(...)):
    result = run_agent(code)
    return {"result": result}


# =========================
# FILE INPUT
# =========================
@app.post("/run-agent/files")
async def run_files(files: List[UploadFile] = File(...)):
    combined_code = ""

    for file in files:
        content = await file.read()
        combined_code += f"\n# FILE: {file.filename}\n"
        combined_code += content.decode()

    result = run_agent(combined_code)
    return {"result": result}