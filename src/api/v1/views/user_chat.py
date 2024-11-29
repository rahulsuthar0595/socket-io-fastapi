from fastapi import APIRouter, Request

router = APIRouter(prefix="/user-chat")


@router.get("/")
async def chat_template(request: Request):
    from app import templates

    return templates.TemplateResponse(
        request=request, name="user_chat.html", context={}
    )

