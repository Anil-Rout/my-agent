# System routes - returns PC information
from fastapi import APIRouter
from actions.system_info import get_cpu, get_ram, get_disk, get_all_info, get_running_processes

router = APIRouter()

@router.get("/info")
def system_info():
    return {"info": get_all_info()}

@router.get("/processes")
def processes():
    return {"processes": get_running_processes()}
