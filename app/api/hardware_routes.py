from fastapi import APIRouter, HTTPException
from app.mock_hardware.state import home_state
from app.models.schemas import HardwareLightPatch, HardwareWindowPatch

router = APIRouter(prefix="/hardware", tags=["Mock Hardware / Demo"])


@router.get("/state")
async def get_state():
    return home_state.snapshot()


@router.post("/windows/state")
async def set_window_state(request: HardwareWindowPatch):
    if request.window_id not in home_state.windows:
        raise HTTPException(status_code=404, detail="Unknown window")
    home_state.windows[request.window_id] = request.status
    return {"success": True, "state": home_state.snapshot()}


@router.post("/lights/state")
async def set_light_state(request: HardwareLightPatch):
    if request.room_id not in home_state.lights:
        raise HTTPException(status_code=404, detail="Unknown room")
    home_state.lights[request.room_id] = request.on
    return {"success": True, "state": home_state.snapshot()}


@router.post("/reset")
async def reset_home():
    home_state.reset()
    return {"success": True, "state": home_state.snapshot()}
