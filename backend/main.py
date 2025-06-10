import logging
import os
import pkgutil
import sys
from functools import wraps
from typing import Callable

import uvicorn
from common import templates
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import (HTMLResponse, JSONResponse, RedirectResponse,
                               Response)
from fastapi.staticfiles import StaticFiles

# from tasks.notion_poller import poll_notion_projects
os.makedirs("log", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("log/app.log", "a", "utf-8"),
    ],
)
logger = logging.getLogger("NoityPy-Backend")
logger.info("Starting NotiPy Backend...")

# 1) fastapi 메인앱, api 용 서브앱 선언
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static", StaticFiles(directory="web/static"), name="static")

COUNTRY_TO_LANG = {
    "KR": "ko",
    # 필요시 더 추가
}


def redirect_to_lang_index(default_lang: str = "en"):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            cookies = request.cookies
            # 쿠키 사용에 동의하지 않은 경우 → 그냥 원래 함수 실행
            if cookies.get("cookiesAccepted") != "true":
                return await func(request, *args, **kwargs)
            lang = cookies.get("lang")
            # lang 쿠키가 없으면 CF-IPCountry로 판단
            if not lang:
                country_code = request.headers.get("CF-IPCountry", "").upper()
                lang = COUNTRY_TO_LANG.get(country_code, default_lang)
            # lang이 결정되었으니 리디렉션
            return RedirectResponse(url=f"/{lang}/index")

        return wrapper

    return decorator


@app.get("/")
@redirect_to_lang_index()
async def root(request: Request):
    return HTMLResponse("<p>Redirecting...</p>")  # fallback (거의 안 씀)


@app.get("/{page}")
async def fallback_lang_redirect(request: Request, page: str):
    lang = request.cookies.get("lang")
    accepted = request.cookies.get("cookiesAccepted")
    if accepted == "true" and lang:
        # 쿠키가 있다면 쿠키에 맞춰 리디렉션
        return RedirectResponse(url=f"/{lang}/{page}")
    # 쿠키 없거나 동의하지 않았으면 → 영어 페이지로 리디렉션
    return RedirectResponse(url=f"/en/{page}")


@app.get("/{lang}/{page}")
async def page_handler(
        request: Request,
        lang: str = "ko",
        page: str = "index"):
    try:
        return templates.TemplateResponse(
            f"{lang}/{page}.html", {"request": request}, status_code=200
        )
    except Exception as e:
        logging.error(f"Error rendering page {lang}/{page}: {e}")
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )


@app.post("/accept-cookies")
async def accept_cookies(request: Request):
    country = request.headers.get("CF-IPCountry", "").upper()
    lang = COUNTRY_TO_LANG.get(country, "en")

    response = JSONResponse({"lang": lang})
    response.set_cookie("cookiesAccepted", "true", max_age=60 * 60 * 24 * 365)
    response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365)
    return response


@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse(
        "404.html", {"request": request}, status_code=404)


@api.exception_handler(RequestValidationError)
async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


# 3) 메인 실행부: 자동으로 routers 폴더 내에 존재하는 모든 라우터 api에 장착
if __name__ == "__main__":
    routers = []
    for loader, module_name, is_pkg in pkgutil.iter_modules(
            ["./routers"], "routers."):
        routers.append(module_name)
    for router in routers:
        module = __import__(router, fromlist=["router"])
        api.include_router(module.router)
    app.mount("/api", api)
    port = int(os.environ.get("BACKEND_PORT", 9091))
    uvicorn.run(app, host="0.0.0.0", port=port)
