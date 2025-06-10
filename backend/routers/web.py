from common import *
from common import templates
from fastapi import *
from fastapi.responses import *
from pydantic import BaseModel
from services import webservice

router = APIRouter(prefix="/web", tags=["Web"])


@router.get("/lang-popup")
async def lang_popup(request: Request):
    """Return the language selection popup."""
    return templates.TemplateResponse("lang-popup.html", {"request": request})


@router.post("/lang")
async def change_lang(response: Response, lang: str = Body(...)):
    # lang 쿠키 설정 (1년 유지)
    response.set_cookie(
        key="lang",
        value=lang,
        max_age=60 * 60 * 24 * 365,  # 1년
        path="/",
        httponly=False,  # JS에서 접근 가능
    )

    return {"status": "ok"}


class notificationClass(BaseModel):
    title: str
    body: str


@router.post("/notification")
async def post_notification(
    request: Request, notification: notificationClass, conn=Depends(get_db)
):
    """
    create a notification for the webpabe.
    """
    auth = request.cookies.get("token")
    print(f"token: {auth}")
    token = await webservice.get_token(conn)
    if not auth or auth != token:
        return JSONResponse(
            {"success": False, "message": "Unauthorized"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    await webservice.notification_post(conn, notification.title, notification.body)
    return JSONResponse(
        {"success": True, "message": "Notification sent successfully"})


@router.get("/notification")
async def get_notification(request: Request, conn=Depends(get_db)):
    """
    Get all notifications for the webpage.
    """
    notifications = await webservice.get_notification(conn)
    notifications = [n.todict() for n in notifications]
    notifications = [
        {**n, "created_at": n["created_at"].split(" ")[0]} for n in notifications
    ]
    return templates.TemplateResponse(
        "noticeitem.html", {"request": request, "notifications": notifications}
    )


@router.get("/upcoming")
async def get_upcoming(request: Request):
    """
    Get all upcoming events for the webpage.
    """
    return templates.TemplateResponse("todo.html", {"request": request})


@router.get("/token")
@checkInternalServer
async def get_token(request: Request, conn=Depends(get_db)):
    """
    Get the token for the webpage.
    if expired, generate a new one.
    """
    token = await webservice.get_token(conn)
    return JSONResponse({"success": True, "token": token})


@router.post("/token/check")
async def check_token(
        request: Request,
        token: str = Body(...),
        conn=Depends(get_db)):
    """
    Check if the token is valid.
    """
    admin = await webservice.get_token(conn)
    if admin == token:
        response = JSONResponse({"success": True, "token": token})
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=3600,
        )
        return response
    else:
        return JSONResponse(
            {"success": False, "message": "Token is invalid"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


@router.post("/logout")
async def logout(request: Request):
    """
    Logout the user by clearing the token cookie.
    """
    response = JSONResponse(
        {"success": True, "message": "Logged out successfully"})
    response.delete_cookie(key="token")
    return response
