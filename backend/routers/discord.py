from common import *
from fastapi import (APIRouter, BackgroundTasks, Body, Depends, HTTPException,
                     Request, Response, status)
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services import discordservice, notionservice, webservice

router = APIRouter(prefix="/discord", tags=["Discord"])


@router.get("/{serverid}")
@checkInternalServer
async def get_server(
    request: Request, serverid: int, eager_load: int = 0, conn=Depends(get_db)
):
    """
    Get a Discord server by its ID.
    """
    server = await discordservice.get_discord_server(conn, serverid, bool(eager_load))
    if not server:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse({"success": True, "server": server.todict()})


@router.post("/clean")
@checkInternalServer
async def add_server(
    request: Request, serverids: list[int] = Body(...), conn=Depends(get_db)
):
    """
    Update or add a Discord server to the database.
    """
    await discordservice.mark_and_clean_discord_servers(conn, serverids)
    return JSONResponse({"success": True})


@router.post("/{serverid}")
@checkInternalServer
async def add_server(request: Request, serverid: int, conn=Depends(get_db)):
    """
    add a Discord server to the database.
    """
    server = await discordservice.get_discord_server(conn, serverid)
    if server:
        return JSONResponse({"success": True, "server": server.todict()})
    server = await discordservice.create_discord_server(conn, serverid)
    return JSONResponse({"success": True, "server": server.todict()})


@router.delete("/{serverid}")
@checkInternalServer
async def remove_server(request: Request, serverid: int, conn=Depends(get_db)):
    await discordservice.remove_discord_server(conn, serverid)
    return JSONResponse({"success": True})


@router.get("/{serverid}/modrole")
@checkInternalServer
async def get_mod_role(request: Request, serverid: int, conn=Depends(get_db)):
    """
    Get the mod role for a Discord server.
    """
    modrole = await discordservice.get_mod_role(conn, serverid)
    if not modrole:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse({"success": True, "modrole": modrole})


@router.put("/{serverid}/modrole")
@checkInternalServer
async def set_mod_role(
        request: Request,
        serverid: int,
        roleid: int = Body(...),
        conn=Depends(get_db)):
    """
    Set the mod role for a Discord server.
    """
    server = await discordservice.set_mod_role(conn, serverid, roleid)
    if not server:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse({"success": True, "server": server.todict()})


@router.put("/{serverid}/webhookchannel")
@checkInternalServer
async def set_webhook_channel(
        request: Request,
        serverid: int,
        channelid: int = Body(...),
        conn=Depends(get_db)):
    """
    Set the webhook channel for a Discord server.
    """
    server = await discordservice.set_webhook_channel(conn, serverid, channelid)
    if not server:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse({"success": True, "server": server.todict()})


@router.get("/{serverid}/notion/database")
@checkInternalServer
async def get_notion_database(
        request: Request,
        serverid: int,
        conn=Depends(get_db)):
    """
    Get the Notion database for a Discord server.
    """
    database = await discordservice.get_notion_database(conn, serverid)
    if not database:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    database = [db.todict() for db in database]
    return JSONResponse({"success": True, "database": database})


@router.get("/{serverid}/notion/token")
@checkInternalServer
async def get_token(request: Request, serverid: int, conn=Depends(get_db)):
    """
    Get the Notion token.
    """
    # Fetch the token from the database
    token = await notionservice.get_notion_token(conn, serverid)
    if not token:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT)  # 204 No Content
    return JSONResponse(content={"status": "success", "token": token})


@router.put("/{serverid}/notion/token")
@checkInternalServer
async def set_token(
        request: Request,
        serverid: int,
        token: str = Body(None),
        conn=Depends(get_db)):
    """
    Set the Notion token.
    """
    await notionservice.set_notion_token(conn, serverid, token)
    return JSONResponse(
        content={"status": "success", "message": "Token set successfully"}
    )


@router.get("/{serverid}/notion/tag")
@checkInternalServer
async def get_notion_tag(
        request: Request,
        serverid: int,
        conn=Depends(get_db)):
    """
    Get the Notion tag for a Discord server.
    """
    tag = await discordservice.get_notion_tag(conn, serverid)
    if not tag:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    tag = [tag.todict() for tag in tag]
    return JSONResponse({"success": True, "tag": tag})


@router.post("/{serverid}/notion/tag")
@checkInternalServer
async def add_notion_tag(
    request: Request, serverid: int, tag: str = Body(...), conn=Depends(get_db)
):
    """
    Set the Notion tag for a Discord server.
    """
    current_tags = await discordservice.get_notion_tag(conn, serverid)
    if len(current_tags) >= 3:
        raise HTTPException(
            status_code=429,
            detail="max_tags_exceeded",
        )
    # 태그가 이미 존재하는지 확인
    existing_tag = next((t for t in current_tags if t.tag == tag), None)
    if existing_tag:
        raise HTTPException(
            status_code=429,
            detail="duplicate_tag",
        )
    # 태그 추가
    tag_obj = await discordservice.add_notion_tag(conn, serverid, tag)
    if not tag_obj:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse({"success": True, "tag": tag_obj.tag})


@router.delete("/{serverid}/notion/tag/{tagname}")
@checkInternalServer
async def remove_notion_tag(
    request: Request, serverid: int, tagname: str, conn=Depends(get_db)
):
    """
    Remove the Notion tag for a Discord server.
    """
    await discordservice.remove_notion_tag(conn, serverid, tagname)
    return JSONResponse({"success": True})


class notificationClass(BaseModel):
    title: str
    body: str


@router.post("/notification")
@checkInternalServer
async def post_notification(
    request: Request, notification: notificationClass, conn=Depends(get_db)
):
    """
    create a notification for the webpabe.
    """
    await webservice.notification_post(conn, notification.title, notification.body)
    return JSONResponse(
        {"success": True, "message": "Notification sent successfully"})
