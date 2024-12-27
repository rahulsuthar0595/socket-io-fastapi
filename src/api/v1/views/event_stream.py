import json
from asyncio import sleep

from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse

router = APIRouter(prefix="/event-stream")


async def waypoints_generator():
    waypoints = open('sample_data.json')
    waypoints = json.load(waypoints)
    for waypoint in waypoints[0: 20]:
        data = json.dumps(waypoint)
        yield f"event: locationUpdate\ndata: {data}\n\n"
        await sleep(0.2)


@router.get("/")
async def event_stream_view(request: Request):
    from app import templates

    return templates.TemplateResponse(
        request=request, name="event_stream.html", context={}
    )


@router.get("/get-data")
async def get_event_stream_data(request: Request):
    return StreamingResponse(waypoints_generator(), media_type="text/event-stream")
