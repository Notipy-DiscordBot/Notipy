from fastapi import FastAPI
from routers import discord, llm, notion, user, web

"""
이 파일은 FastAPI 를 파이참 환경에서 테스트하고 수정하기 위한 파일입니다.
"""


app = FastAPI()
api = FastAPI()

app.mount("/api", api)
api.include_router(user.router)
api.include_router(discord.router)
api.include_router(notion.router)
api.include_router(llm.router)
api.include_router(web.router)
