from fastapi import APIRouter, Request

router = APIRouter(prefix="/chat")


@router.get("/")
async def chat_template(request: Request):
    from app import templates

    return templates.TemplateResponse(
        request=request, name="socket_io.html", context={}
    )


@router.get("/admin")
async def admin_template(request: Request):
    from app import templates

    return templates.TemplateResponse(
        request=request, name="socket_io.html", context={}
    )
