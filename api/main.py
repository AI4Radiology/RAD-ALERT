from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import json
import uuid
from .settings import tools_settings as settings
from .processing import process_report
from .notifications  import send_whatsapp

app = FastAPI(debug=settings.DEBUG)

@app.post("/hl7")
async def receive_hl7(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    report    = data.get("report", "")
    report_id = data.get("reportId") or str(uuid.uuid4())
    background_tasks.add_task(process_report, report, report_id)
    return JSONResponse({"ack": "bien recibido", "report_id": report_id})
