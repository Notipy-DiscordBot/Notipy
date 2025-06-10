import asyncio
import importlib
import json
import logging
import os
import pkgutil
import sys
import traceback
from contextlib import asynccontextmanager
from typing import Callable

import commons
from commons import MyFunctions, localizator
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse
from interactions import (AutocompleteContext, Client, Intents, OptionType,
                          SlashContext, check, global_autocomplete, listen,
                          slash_command, slash_option)
from interactions.api.events import CommandError, ComponentError, Startup
from interactions.client.errors import (CommandCheckFailure, CommandOnCooldown,
                                        Forbidden, MaxConcurrencyReached)

debugMode = False


class MyLogger(logging.Logger):
    def __init__(self, name):
        self.conn = None
        self.broadcastlevel = "info"
        super(MyLogger, self).__init__(name)

    def debug(self, msg, *args, **kwargs):
        return super(MyLogger, self).debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        return super(MyLogger, self).info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return super(MyLogger, self).error(msg, *args, **kwargs)


logging.setLoggerClass(MyLogger)
logging.basicConfig()

logger = logging.getLogger("notipy")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

debugfile = commons.logfilepath + commons.debugfile
file_debug_handler = logging.FileHandler(debugfile, encoding="utf-8", mode="w")
file_debug_handler.setLevel(logging.DEBUG)
file_debug_handler.setFormatter(formatter)
logger.addHandler(file_debug_handler)

errlogfile = commons.logfilepath + commons.errfile
file_error_handler = logging.FileHandler(
    errlogfile, encoding="utf-8", mode="a")
file_error_handler.setLevel(logging.ERROR)
file_error_handler.setFormatter(formatter)
logger.addHandler(file_error_handler)

bot = Client(
    intents=Intents.DEFAULT | Intents.MESSAGE_CONTENT | Intents.GUILD_MEMBERS,
    sync_interactions=True,
    fetch_members=True,
    logger=logger,
    # send_default_errors=False,
    delete_unused_application_cmds=True,
    activity="DM으로 문의하세요!",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.isdir(commons.logfilepath):
        os.makedirs(commons.logfilepath)
    if debugMode:
        bot.debug_scope = commons.devserver
        logger.info("Bot starting.in debug mode")
    asyncio.create_task(bot.astart(commons.token))
    yield


app = FastAPI(lifespan=lifespan, root_path=commons.app_root)


@listen(ComponentError, disable_default_listeners=True)
async def my_component_error_handler(event: ComponentError):
    """
    Handles component errors.
    """
    ctx = event.ctx
    locale = ctx.locale
    _ = localizator(locale)
    error = event.error
    bot.logger.warning(error)
    if isinstance(event.error, CommandCheckFailure):
        await ctx.send(_("check_failed_err"), ephemeral=True, components=[])
        return
    elif isinstance(event.error, Forbidden):
        await ctx.send(_("missing_permission_err"), ephemeral=True, components=[])
        return
    elif isinstance(event.error, CommandOnCooldown):
        err: CommandOnCooldown = event.error
        await ctx.send(
            _("command_on_cooldown_err").format(
                round(err.cooldown.get_cooldown_time())
            ),
            ephemeral=True,
        )
        return
    else:
        logger.error(error)
        logger.error(traceback.print_exception(error))
        json = {
            "serverid": ctx.guild.id,
            "userid": ctx.author.id,
            "component": ctx.component.custom_id,
            "error": str(error),
        }
        # erridx = await apirequest("/error/add", json=json)
        # await ctx.send(f"에러가 발생했습니다.\n에러번호: `{erridx['data']}`",
        # ephemeral=True)
        await ctx.send(_("error_occurred_err"), ephemeral=True, components=[])
        logger.error("에러가 발생했습니다.")
        logger.error(json)


@listen(CommandError, disable_default_listeners=True)
async def my_error_handler(event: CommandError):
    """
    Handles command errors.
    """
    ctx = event.ctx
    locale = ctx.locale
    _ = localizator(locale)
    error = event.error
    bot.logger.warning(error)
    if isinstance(event.error, CommandCheckFailure):
        await ctx.send(_("check_failed_err"), ephemeral=True, components=[])
        return
    elif isinstance(event.error, CommandOnCooldown):
        err: CommandOnCooldown = event.error
        await ctx.send(
            _("command_on_cooldown_err").format(
                round(err.cooldown.get_cooldown_time())
            ),
            ephemeral=True,
        )
        return
    elif isinstance(event.error, MaxConcurrencyReached):
        await ctx.send(_("max_concurrency_err"), ephemeral=True, components=[])
        return
    elif isinstance(event.error, Forbidden):
        await ctx.send(_("missing_permission_err"), ephemeral=True, components=[])
    else:
        logger.error(error)
        logger.error(traceback.print_exception(error))
        json = {
            "serverid": ctx.guild.id,
            "userid": ctx.author.id,
            "command": ctx.command.name.get_locale("korean"),
            "error": str(error),
        }
        # erridx = await apirequest("/error/add", json=json)
        # await ctx.send(f"에러가 발생했습니다.\n에러번호: `{erridx['data']}`",
        # ephemeral=True)
        await ctx.send(_("error_occurred_err"), ephemeral=True)
        logger.error("에러가 발생했습니다.")
        logger.error(json)


Extensions = []


def update_extensions():
    global Extensions
    Extensions = []
    for loader, module_name, is_pkg in pkgutil.iter_modules(
        ["./extensions"], "extensions."
    ):
        Extensions.append(module_name)
    Extensions.append("all")


def reloadpip():
    importlib.reload(commons)


@listen(Startup)
async def on_startup():
    """
    on startup, load up all extesions
    """
    update_extensions()
    for temp in Extensions:
        if temp == "all":
            continue
        bot.load_extension(temp, functions=functions)
    logger.info("Bot is ready")
    logger.error("Bot is ready")
    if debugMode:
        for guild in bot.guilds:
            if int(guild.id) != int(commons.devserver):
                logger.info(f"Leaving guild {guild.name} ({guild.id})")
                await guild.leave()


@slash_command(name="hello", description="Hello", scopes=[commons.devserver])
async def my_command_function(ctx: SlashContext):
    await ctx.send("안녕", ephemeral=True)


def extension():
    """Call with `@extension()`"""

    def wrapper(func):
        return slash_option(
            name="extension",
            description="extension name",
            opt_type=OptionType.STRING,
            required=True,
            autocomplete=True,
        )(func)

    return wrapper


@check(commons.is_dev)
@slash_command(
    name="load_ext", description="load extension", scopes=[commons.devserver]
)
@extension()
async def loadext(ctx: SlashContext, extension: str):
    reloadpip()
    if extension == "all":
        for temp in Extensions:
            if temp == "all":
                continue
            bot.load_extension(temp, functions=functions)
    else:
        bot.load_extension(extension, functions=functions)
    await ctx.send("Done", ephemeral=True)


@check(commons.is_dev)
@slash_command(name="unload_ext",
               description="unload extension",
               scopes=[commons.devserver])
@extension()
async def unloadext(ctx: SlashContext, extension: str):
    print(extension)
    if extension == "all":
        for temp in Extensions:
            if temp == "all":
                continue
            bot.unload_extension(temp)
    else:
        bot.unload_extension(extension)
    await ctx.send("Done", ephemeral=True)


@check(commons.is_dev)
@slash_command(name="reload_ext",
               description="reload extension",
               scopes=[commons.devserver])
@extension()
async def reloaddext(ctx: SlashContext, extension: str):
    reloadpip()
    if extension == "all":
        for temp in Extensions:
            if temp == "all":
                continue
            bot.unload_extension(temp)
            bot.load_extension(temp, functions=functions)
    else:
        bot.unload_extension(extension)
        bot.load_extension(extension, functions=functions)
    await ctx.send("Done", ephemeral=True)


@check(commons.is_dev)
@slash_command(
    name="reload_extensionlist",
    description="reloads list of extensions",
    scopes=[commons.devserver],
)
async def reload_extensionlist(ctx: SlashContext):
    update_extensions()
    await ctx.send("Done", ephemeral=True)


@global_autocomplete("extension")
async def autocomplete(ctx: AutocompleteContext):
    await ctx.send(choices=Extensions)


functions = MyFunctions(logger)


@app.get("/call/{functionname}")
async def discordbot(request: Request, functionname: str, params: str = None):
    """
    FastAPI endpoint to call discordbot functions
    :param functionname: name of the function to call
    :param params: parameters to pass to the function
    :return: result of the function

    진짜 이상한데 일단 되긴 함
    주로 백엔드에서 디스코드 봇에 있는 함수를 호출할 때 사용됨
    """
    if request.headers.get("X-Internal-Request") != "true":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    # params: json string
    params = params or "{}"
    # Check if the function exists in the bot
    if not hasattr(functions, functionname):
        return JSONResponse({"error": "Function not found"})
    # Run the function
    result = await functions.run(
        functionname, bot, json.loads(params)
    )  # this enables function to use params as kwargs
    return JSONResponse(result)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 9090))
    if int(os.environ.get("DEBUG", 0)) == 1:
        debugMode = True
    uvicorn.run(app, host="0.0.0.0", port=port)
