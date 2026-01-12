from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from recorder import Recorder, Runner, DrissionRunner
from ai_agent import modify_workflow
import asyncio
import logging
from typing import List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_recorder: Optional[Recorder] = None


class StartRecordingRequest(BaseModel):
    url: str


class WorkflowRunRequest(BaseModel):
    url: str
    actions: List[Any]
    enable_bypass_mode: bool = False


class WorkflowModificationRequest(BaseModel):
    current_flow: List[Any]
    user_prompt: str


@app.post("/record/start")
async def start_recording(request: StartRecordingRequest):
    global active_recorder
    try:
        if active_recorder:
            await active_recorder.stop_recording()

        active_recorder = Recorder()
        asyncio.create_task(active_recorder.start_recording(request.url))

        return {"status": "started", "url": request.url}
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ManualEventRequest(BaseModel):
    type: str
    selector: str
    value: Optional[str] = ""


@app.post("/record/event")
async def add_manual_event(event: ManualEventRequest):
    global active_recorder
    if not active_recorder:
        raise HTTPException(status_code=400, detail="Recording not active")

    event_data = {
        "type": event.type,
        "selector": event.selector,
        "value": event.value,
        "timestamp": 0,
    }
    active_recorder.events.append(event_data)
    logger.info(f"Manually added event: {event_data}")
    return {"status": "added", "event": event_data}


@app.get("/record/events")
async def get_events():
    global active_recorder
    if not active_recorder:
        return []
    return active_recorder.events


@app.post("/record/stop")
async def stop_recording():
    global active_recorder
    try:
        if active_recorder:
            events = active_recorder.events
            await active_recorder.stop_recording()
            return {"status": "stopped", "events": events}
        return {"status": "error", "message": "No active recording"}
    except Exception as e:
        logger.error(f"Failed to stop recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/modify-workflow")
async def modify_workflow_endpoint(request: WorkflowModificationRequest):
    try:
        commands = modify_workflow(request.current_flow, request.user_prompt)
        return commands
    except Exception as e:
        logger.error(f"Failed to modify workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run")
async def run_workflow_endpoint(request: WorkflowRunRequest):
    try:
        if request.enable_bypass_mode:
            runner = DrissionRunner()
            asyncio.create_task(
                asyncio.to_thread(runner.run_workflow, request.url, request.actions)
            )
            mode = "bypass"
        else:
            runner = Runner()
            asyncio.create_task(runner.run_workflow(request.url, request.actions))
            mode = "standard"

        return {"status": "running", "mode": mode}
    except Exception as e:
        logger.error(f"Failed to run workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ManualEventRequest(BaseModel):
    type: str
    selector: str
    value: Optional[str] = ""


@app.post("/record/event")
async def add_manual_event(event: ManualEventRequest):
    global active_recorder
    if not active_recorder:
        raise HTTPException(status_code=400, detail="Recording not active")

    event_data = {
        "type": event.type,
        "selector": event.selector,
        "value": event.value,
        "timestamp": 0,
    }
    active_recorder.events.append(event_data)
    logger.info(f"Manually added event: {event_data}")
    return {"status": "added", "event": event_data}


@app.get("/record/events")
async def get_events():
    global active_recorder
    if not active_recorder:
        return []
    return active_recorder.events


@app.post("/record/stop")
async def stop_recording():
    global active_recorder
    try:
        if active_recorder:
            events = active_recorder.events
            await active_recorder.stop_recording()
            return {"status": "stopped", "events": events}
        return {"status": "error", "message": "No active recording"}
    except Exception as e:
        logger.error(f"Failed to stop recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/modify-workflow")
async def modify_workflow_endpoint(request: WorkflowModificationRequest):
    try:
        commands = modify_workflow(request.current_flow, request.user_prompt)
        return commands
    except Exception as e:
        logger.error(f"Failed to modify workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run")
async def run_workflow_endpoint(request: WorkflowRunRequest):
    try:
        if request.enable_bypass_mode:
            runner = DrissionRunner()
            # Run blocking code in thread
            asyncio.create_task(
                asyncio.to_thread(runner.run_workflow, request.url, request.actions)
            )
            mode = "bypass"
        else:
            runner = Runner()
            asyncio.create_task(runner.run_workflow(request.url, request.actions))
            mode = "standard"

        return {"status": "running", "mode": mode}
    except Exception as e:
        logger.error(f"Failed to run workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))
