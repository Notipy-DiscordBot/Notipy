from datetime import datetime
from functools import partial, wraps

from common import *
from fastapi import (APIRouter, BackgroundTasks, Body, Depends, Request,
                     Response, status)
from fastapi.responses import JSONResponse, RedirectResponse
from services import userservice as crud

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/")
async def root(request: Request):
    print(request.headers)
    return JSONResponse(content={"message": "Hello World from User!"})


@router.get("/get")
@checkInternalServer
async def get(
    request: Request,
    discordid: int,
    serverid: int = None,
    other: int = 0,
    conn=Depends(get_db),
):
    """
    Get user information by discord id
    :param discordid: Discord ID of the user
    :param serverid: Server ID to check if the user is allowed to see the information
    :param other: If the user requested is not the same as the user making the request
    :param conn: Database connection
    :return: JSON response with user information
    """
    if other:
        res = await crud.get_git_show(conn, discordid, serverid)
        if res is None:  # if res is None, it means the user does not exist
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        if not res:  # if res is false
            return Response(status_code=status.HTTP_403_FORBIDDEN)
    res = await crud.get_user(conn, discordid)
    if res is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    user, github, notion = res
    returnval = {
        "user": user.todict(),
        "github": None,
        "notion": None,
        "repos": None}
    if github:
        returnval["github"] = github.todict()
        if github.primary_languages:
            repos = await crud.get_repositories(conn, github.github_id)
            returnval["repos"] = [repo.todict() for repo in repos]
    if notion:
        returnval["notion"] = notion.todict()
    return JSONResponse(content=returnval)


def checkTokenExpired(func):
    """
    Decorator to check if the token is expired.
    """

    @wraps(func)
    async def wrapper(conn, tokens: crud.Tokens):
        user = await crud.get_user_by_token(conn, access_token=tokens.access_token)
        refreshed = True
        if user:
            refreshed = False
            if user.token_expires is not None:
                if user.token_expires < datetime.now():
                    tokens = await refresh_token(tokens)
                    refreshed = True
        return await func(conn, tokens, refreshed)

    return wrapper


@router.get("/auth")
async def auth(
        code: str,
        background_tasks: BackgroundTasks,
        conn=Depends(get_db)):
    """
    Authenticates the user with Discord using the provided code.
    :param code: The authorization code received from Discord
    :return: JSON response with the access token and user information
    """
    background_tasks.add_task(exchange_code, conn=conn, code=code)
    return RedirectResponse(url="/oauth-success")


async def exchange_code(conn, code: str):
    """
    Exchanges the authorization code for an access token.
    """
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    status, response = await make_request(
        "POST",
        f"{DISCORD_API_ENDPOINT}/oauth2/token",
        data=data,
        headers=headers,
        auth=discord_auth,
    )
    if status != 200:
        return
    access_token = response["access_token"]
    refresh_token = response["refresh_token"]
    expires_in = response["expires_in"]
    tokens = crud.Tokens(access_token, refresh_token, expires_in)
    await get_user_info(conn, tokens)


async def refresh_token(tokens: crud.Tokens) -> crud.Tokens:
    """
    Refreshes the access token using the refresh token.
    """
    data = {
        "grant_type": "refresh_token",
        "refresh_token": tokens.refresh_token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    status, response = await make_request(
        "POST",
        f"{DISCORD_API_ENDPOINT}/oauth2/token",
        data=data,
        headers=headers,
        auth=discord_auth,
    )
    if status != 200:
        return
    access_token = response["access_token"]
    refresh_token = response["refresh_token"]
    expires_in = response["expires_in"]
    tokens = crud.Tokens(access_token, refresh_token, expires_in)
    return tokens


@checkTokenExpired
async def get_user_info(conn, tokens: crud.Tokens, refreshed: bool = False):
    """
    Retrieves user information from Discord using the access token.
    Then uses github id and github api to and login.
    store github id and login in database.
    :param tokens: tokens object containing access_token, refresh_token and expires_in
    :param refreshed: if the token was refreshed
    """
    headers = {"Authorization": f"Bearer {tokens.access_token}"}
    status, response = await make_request(
        "GET", f"{DISCORD_API_ENDPOINT}/users/@me", headers=headers
    )
    if status != 200:
        return
    discordid = int(response["id"])
    if refreshed:
        await crud.setTokens(conn, discordid, tokens)
    status, response = await make_request(
        "GET", f"{DISCORD_API_ENDPOINT}/users/@me/connections", headers=headers
    )
    if status != 200:
        return
    githubid = None
    for i in response:
        if i["type"] == "github":
            githubid = i["id"]
            break
    # headers = {"Authorization": "Bearer " + GITHUB_TOKEN} # Works without
    # this... damn
    status, response = await make_request(
        "GET", f"{GITHUB_API_ENDPOINT}/user/{githubid}"
    )
    if status != 200:
        return
    gitlogin = response["login"]
    await crud.link_github(conn, discordid, githubid, gitlogin)
    return response


@router.get("/forumthread")
@checkInternalServer
async def get_forum_channel(
        request: Request,
        userid: int,
        conn=Depends(get_db)):
    """
    Get the forum channel for a user.
    :param userid: Discord ID of the user
    :param conn: Database connection
    :return: JSON response with forum channel information
    """
    channel = await crud.get_forum_channel(conn, userid)
    return JSONResponse({"success": True, "channel": channel.channel_id})


@router.put("/forumthread/{userid}/block")
@checkInternalServer
async def toggle_block_forum_channel(
    request: Request, userid: int, conn=Depends(get_db)
):
    """
    Block the forum thread for a user.
    :param userid: Discord ID of the user
    :param conn: Database connection
    :return: JSON response indicating success
    """
    await crud.toggle_block_forum_channel(conn, userid)
    return JSONResponse({"success": True, "message": "Forum thread blocked"})


@router.put("/forumthread/{userid}/channelid")
@checkInternalServer
async def set_forum_thread_channel(
        request: Request,
        userid: int,
        channelid: int = Body(...),
        conn=Depends(get_db)):
    """
    Set the forum thread channel for a user.
    :param userid: Discord ID of the user
    :param channelid: Channel ID to set for the forum thread
    :param conn: Database connection
    :return: JSON response indicating success
    """
    await crud.set_forum_thread_channel(conn, userid, channelid)
    return JSONResponse(
        {"success": True, "message": "Forum thread channel set"})


@router.get("/forumthread/bychannel")
@checkInternalServer
async def get_forum_thread_by_channel(
    request: Request, channelid: int, conn=Depends(get_db)
):
    """
    Get the forum thread by channel ID.
    :param channelid: Channel ID of the forum thread
    :param conn: Database connection
    :return: JSON response with forum thread information
    """
    thread = await crud.get_forum_thread_by_channel(conn, channelid)
    if not thread:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse({"success": True, "userid": thread.user_id})


@router.delete("/forumthread/{userid}")
@checkInternalServer
async def delete_forum_thread(
        request: Request,
        userid: int,
        conn=Depends(get_db)):
    """
    Delete the forum thread for a user.
    :param userid: Discord ID of the user
    :param conn: Database connection
    :return: JSON response indicating success
    """
    await crud.delete_forum_thread(conn, userid)
    return JSONResponse({"success": True, "message": "Forum thread deleted"})


@router.put("/github/{userid}/toggle")
@checkInternalServer
async def toggle_github(
        request: Request,
        userid: int,
        serverid: int = Body(...),
        conn=Depends(get_db)):
    """
    Toggle the GitHub connection for a user.
    :param userid: Discord ID of the user
    :param conn: Database connection
    :return: JSON response indicating success
    """
    show = await crud.toggle_github_show(conn, serverid, userid)
    if show is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse({"success": True, "data": show.show})
