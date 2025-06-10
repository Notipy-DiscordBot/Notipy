import inspect
import random
from http.client import responses
from os.path import abspath, dirname
from typing import Any, Awaitable, Callable, Coroutine, Optional, Tuple

import aiohttp
from cachetools import TTLCache
from interactions import (ActionRow, BaseComponent, BaseContext,
                          ChannelSelectMenu, Client, Message, RoleSelectMenu,
                          StringSelectMenu)
from interactions.api.events import Component

from .cache import BiDirectionalTTLCache
from .locale import *
from .Options import *
from .var import *

wd = dirname(
    abspath(__file__)
)  # 현재 작업 디렉토리 (discordbot/commons/localization.py의 위치)
rootdir = dirname(
    dirname(abspath(__file__))
)  # 현재 작업 디렉토리 (discordbot/main.py의 위치)
logfilepath = rootdir + "/logs/"  # 로그 파일 경로
AsyncFuncType = Callable[..., Coroutine[Any, Any, Any]]


async def is_dev(ctx) -> bool:
    return int(ctx.author.id) in developers


modcache = TTLCache(maxsize=100, ttl=60 * 60 * 24)  # 1일 캐시


async def is_moderator(ctx: BaseContext) -> bool:
    if ctx.guild is None:
        return False
    guild = ctx.guild
    member = await guild.fetch_member(ctx.author.id)
    if member.guild_permissions.ADMINISTRATOR:
        return True
    member_role_ids = [int(role.id) for role in member.roles]
    # TODO: use cache, 나중에 cachetools로 캐시 구현 예정
    # cached_modrole_id = modcache.get(guild.id)
    # if cached_modrole_id is not None:
    #     return cached_modrole_id in member_role_ids
    status, response = await apirequest(f"/discord/{guild.id}/modrole")
    if status != 200:
        return False
    modrole = response.get("modrole")
    if modrole is None:
        return False
    modrole_id = int(modrole)
    modcache[guild.id] = modrole_id
    return modrole_id in member_role_ids


async def wait_for_component_interaction(
    ctx,
    component: StringSelectMenu | ChannelSelectMenu | RoleSelectMenu | BaseComponent,
    message: Message,
    timeout: int = 60,
    check: Optional[Callable[[Component], Awaitable[bool]]] = None,
) -> Optional[Tuple[ComponentContext, Any]]:
    """
    지정한 컴포넌트에 대해 유저의 상호작용을 기다립니다.

    :param ctx: 상호작용 컨텍스트
    :param component: Component 또는 ActionRow 또는 그 리스트
    :param message: 컴포넌트를 포함한 메시지
    :param timeout: 대기 시간 (초)
    :param check: (선택) 추가적인 필터 조건 함수. True를 반환해야 유효한 상호작용으로 간주됨
    :return: 상호작용이 발생한 컴포넌트의 컨텍스트와 값. 타임아웃 시 None을 반환
    """
    try:
        used_component: Component = await ctx.bot.wait_for_component(
            components=component, timeout=timeout, check=check
        )
        returnval = None
        try:
            returnval = used_component.ctx.values[0]
        except IndexError:  # Button 같은 경우
            pass
        return (used_component.ctx, returnval)  # 보통 Select 메뉴일 경우
    except TimeoutError:
        await message.delete(context=ctx)
        return None


class MyFunctions:
    logger = None

    def __init__(self, logger):
        self.logger = logger

    def set(self, name, value: AsyncFuncType) -> None:
        """
        Set the function by name
        :param name: name of the function
        :param value: Async function that will be called
        """
        if not inspect.iscoroutinefunction(value):
            raise ValueError(f"{name} is not a coroutine function")
        setattr(self, name, value)

    def remove(self, name: str) -> None:
        """
        Remove the function by name
        :param name: name of the function
        """
        if hasattr(self, name):
            delattr(self, name)

    def get(self, name) -> AsyncFuncType or None:
        """
        Get the function by name
        :param name: name of the function
        :return: function
        """
        return getattr(self, name)

    async def run(self, name: str, bot: Client, params: dict):
        """
        Run the function by name
        :param name: name of the function
        :param bot: bot instance
        :param params: parameters to pass to the function
        :return: result of the function
        """
        func = self.get(name)
        if func is None:
            return None
        try:
            result = await func(bot, params)
            return result
        except Exception as e:
            self.logger.error(f"Error running function {name}: {e}")
            return None


async def apirequest(
    endpoint: str,
    method: str = "GET",
    params: dict = None,
    data: dict = None,
    json: any = None,
    headers: dict = None,
    auth: aiohttp.BasicAuth = None,
) -> tuple[int, dict | None]:
    return await makerequest(
        api_root + endpoint, method, params, data, json, headers, auth
    )


async def makerequest(
    url: str,
    method: str = "GET",
    params: dict = None,
    data: dict = None,
    json: any = None,
    headers: dict = None,
    auth: aiohttp.BasicAuth = None,
) -> tuple[int, dict | None]:
    # add default_header to headers
    if headers is None:
        headers = {}
    headers["X-Internal-Request"] = (
        "true"  # this is a custom header to identify internal requests
    )
    headers["Content-Type"] = "application/json"
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method,
            url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            auth=auth,
        ) as response:
            status = response.status
            json_res = None
            try:
                json_res = await response.json()
            except aiohttp.ContentTypeError:
                json_res = None
            return status, json_res


def createRandomColor():
    """
    Create a random color in hex format.
    :return: A string representing the color in hex format
    """

    return "#{:06x}".format(random.randint(0, 0xFFFFFF))
