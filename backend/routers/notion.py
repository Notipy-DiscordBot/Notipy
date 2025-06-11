from typing import Optional

from cachetools import TTLCache
from common import *
from fastapi import (APIRouter, BackgroundTasks, Body, Depends, HTTPException,
                     Request)
from fastapi import status as HTTPStatus
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from services import discordservice, notionservice

router = APIRouter(prefix="/notion", tags=["Notion"])


@router.post("/external/databases")
@checkInternalServer
async def fetch_databases(request: Request, token: str = Body(...)):
    """
    get all databases the token has access to
    """
    url = NOTION_API_URL + "/search"
    headers = notionHeaders(token)
    data = {"filter": {"property": "object", "value": "database"}, "query": ""}
    statuscode, response = await make_request(
        url=url, headers=headers, method="POST", json=data, internal=False
    )
    if statuscode != 200:
        raise HTTPException(status_code=statuscode, detail=response)
    return JSONResponse(content={"status": "success", "data": response})


class NotionDatabaseFetchRequest(BaseModel):
    token: str
    databaseid: str


@router.post("/external/database")
@checkInternalServer
async def fetch_database(request: Request, items: NotionDatabaseFetchRequest):
    """
    Fetch the database from Notion.
    """
    url = NOTION_API_URL + f"/databases/{items.databaseid}"
    status, response = await make_request(
        url=url, headers=notionHeaders(items.token), method="GET"
    )
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return JSONResponse(content={"status": "success", "data": response})


class NotionDatabaseLinkRequest(BaseModel):
    serverid: int
    databaseid: str
    databasename: str
    channelid: int


@router.post("/database")
@checkInternalServer
async def notion_database_linked(
    request: Request, items: NotionDatabaseLinkRequest, conn=Depends(get_db)
):
    """
    Link the Notion database to the server.
    """
    res = await notionservice.get_linked_notion_database(conn, items.channelid)
    if res is not None:
        return JSONResponse(
            content={"status": "error", "message": "channel_already_linked"},
            status_code=400,
        )
    await notionservice.link_notion_database(
        conn, items.serverid, items.databaseid, items.databasename, items.channelid
    )
    return JSONResponse(
        content={
            "status": "success",
            "message": "Database linked successfully"})


@router.delete("/database/{databaseid}")
@checkInternalServer
async def delete_database(
        request: Request,
        databaseid: str,
        conn=Depends(get_db)):
    """
    Delete the Notion database.
    """
    # Remove the token from the database
    notiondb = await notionservice.delete_notion_database(conn, databaseid)
    if not notiondb:
        return Response(status_code=HTTPStatus.HTTP_204_NO_CONTENT)
    channelid = notiondb.channel_id
    threadids = [page.thread_id for page in notiondb.pages]
    return JSONResponse(
        content={
            "status": "success",
            "data": {"threads": threadids, "channelid": channelid},
        }
    )


@router.put("/notionpage/{pageid}/threadid")
@checkInternalServer
async def set_thread_id(
        request: Request,
        pageid: str,
        threadid: int = Body(...),
        conn=Depends(get_db)):
    """
    Set the thread ID for the Notion page.
    """
    # Update the thread ID in the database
    res = await notionservice.set_thread_id(conn, pageid, threadid)
    return JSONResponse(
        content={"status": "success", "message": "Thread ID set successfully"}
    )


@router.put("/notionpage/{pageid}/toggleblock")
@checkInternalServer
async def toggle_block(request: Request, pageid: str, conn=Depends(get_db)):
    """
    Toggle the block status of the Notion page.
    """
    # Update the block status in the database
    res = await notionservice.toggle_block_notion_page(conn, pageid)
    if not res:
        return Response(status_code=HTTPStatus.HTTP_204_NO_CONTENT)
    return JSONResponse(content={"status": "success", "data": res.blocked})


@router.post("/notionpage/updated")
@checkInternalServer
async def set_page_updated(
    request: Request, threadids: list[int] = Body(...), conn=Depends(get_db)
):
    await notionservice.set_pages_updated(conn, threadids)
    return JSONResponse(
        content={"status": "success", "message": "Page updated successfully"}
    )


@router.get("/notionpage/updated")
@checkInternalServer
async def get_all_updated(request: Request, conn=Depends(get_db)):
    """
    Get all updated pages from the database.
    """
    res = await notionservice.get_all_updated_pages(conn)
    if not res:
        return Response(status_code=HTTPStatus.HTTP_204_NO_CONTENT)
    returndict = []
    updateddatabase = []
    corrupteddatabases = []
    for row in res:
        page, databaseid, channelid, token, tags = row
        if databaseid in corrupteddatabases:
            continue  # Skip if the database is already marked as corrupted
        if not token:
            continue  # No token found, skip this page
        # Notion 페이지 정보 조회
        if databaseid not in updateddatabase:
            url = NOTION_API_URL + f"/databases/{databaseid}"
            status, response = await make_request(
                url=url, headers=notionHeaders(token), method="GET"
            )
            if status != 200:
                corrupteddatabases.append(databaseid)
                continue
            databasetitle = response["title"][0]["plain_text"]
            await notionservice.set_notion_database_name(
                conn, databaseid, databasetitle
            )
            updateddatabase.append(databaseid)
        # Notion 페이지 정보 파싱
        pagedict = {
            "pageid": page.page_id,
            "threadid": page.thread_id,
            "channelid": channelid,
            "status": True,
            "tags": [],
        }
        pagedata = await get_page_func(page.page_id, token, forcereload=True)
        if pagedata:
            # 페이지 제목과 URL 파싱
            prop = pagedata["properties"]
            pagedict["pageurl"] = pagedata["url"]
            pagedict["props"] = {}
            for item in prop:
                if prop[item]["type"] == "title":
                    if prop[item]["title"]:
                        pagedict["pagetitle"] = prop[item]["title"][0]["plain_text"]
                    else:
                        pagedict["status"] = False
                        continue
                else:
                    match prop[item]["type"]:
                        case "rich_text":
                            pagedict["props"][item] = (
                                prop[item]["rich_text"][0]["plain_text"]
                                if prop[item]["rich_text"]
                                else ""
                            )
                        case "select":
                            pagedict["props"][item] = (
                                prop[item]["select"]["name"]
                                if prop[item]["select"]
                                else ""
                            )
                            if item in tags:
                                pagedict["tags"].append(
                                    pagedict["props"][item]
                                )  # tag for discord forum channel
                        case "multi_select":
                            pagedict["props"][item] = [tag["name"]
                                                       for tag in prop[item]["multi_select"]]
                        case "checkbox":
                            pagedict["props"][item] = prop[item]["checkbox"]
                        case "number":
                            pagedict["props"][item] = prop[item]["number"]
                        case "date":
                            if prop[item]["date"] is not None:
                                start = prop[item]["date"]["start"]
                                end = prop[item]["date"]["end"]
                                if start and end:
                                    pagedict["props"][item] = f"{start} ~ {end}"
                                elif start:
                                    pagedict["props"][item] = start
                                elif end:
                                    pagedict["props"][item] = end
                        case "people":
                            pagedict["props"][item] = [
                                user["name"] for user in prop[item]["people"]
                            ]
                        case "files":
                            pagedict["props"][item] = [
                                file["name"] for file in prop[item]["files"]
                            ]
                        case "url":
                            pagedict["props"][item] = prop[item]["url"]
                        case "status":
                            pagedict["props"][item] = (
                                prop[item]["status"]["name"]
                                if prop[item]["status"]
                                else ""
                            )
                            if item in tags:
                                pagedict["tags"].append(
                                    pagedict["props"][item]
                                )  # tag for discord forum channel
                        case _:
                            # print(f"Unknown type: {prop[item]['type']}")
                            pagedict["props"][item] = prop[item]["type"] + \
                                " under dev"
            # 페이지 정보 추가
            returndict.append(pagedict)
        else:
            pagedict["status"] = False
            await notionservice.remove_notion_page(conn, page.page_id)
            # 페이지 정보를 노션에서 가져오지 못한 경우
            # 주로 페이지가 삭제된 경우 -> 디스코드에서도 적절히 조치

    # 결과를 JSON 형식으로 반환
    return JSONResponse(content={"status": "success", "data": returndict})


@router.post("/webhook/{serverid}")
async def notion_webhook_listener(
    request: Request,
    serverid: int,
    backgroundtask: BackgroundTasks,
    conn=Depends(get_db),
):
    """
    Webhook listener for Notion events, intended to forward the data to a Discord bot.
    """
    # Webhook 요청 본문을 JSON으로 파싱
    data = await request.json()
    backgroundtask.add_task(notion_webhook_handler, data, conn, serverid)
    # Webhook 인증 요청 처리 (verification_token 포함 여부 확인)
    return JSONResponse(content={"message": "Webhook received"})


async def notion_webhook_handler(data, conn, serverid):
    webhookdata = {}
    # 해당 serverid의 Discord 서버 정보 조회 (DB에서)
    server = await discordservice.get_discord_server(conn, serverid)
    webhookdata["channelid"] = (
        server.webhook_channel_id
    )  # 메시지를 보낼 디스코드 채널 ID
    if "verification_token" in data:
        webhookdata["verification_token"] = data["verification_token"]
    else:
        # 일반 웹훅 이벤트 처리
        author = data["authors"][0]["id"]
        webhookdata["avatar_url"] = None
        # Notion 토큰 조회 (서버에 연결된 토큰)
        token = await notionservice.get_notion_token(conn, serverid)
        if not token:
            return JSONResponse(
                content={"status": "error", "message": "No token found"},
                status_code=400,
            )
        # Notion 사용자 정보 조회 (작성자)
        userdata = await get_user_func(author, token)
        if userdata:
            webhookdata["author"] = userdata["name"]
            if userdata["avatar_url"]:
                webhookdata["avatar_url"] = userdata["avatar_url"]
        # 공통 필드 저장
        webhookdata["entity"] = data["entity"]
        webhookdata["type"] = data["type"]
        webhookdata["timestamp"] = data["timestamp"]
        webhookdata["workspace_name"] = data["workspace_name"]
        # 페이지 관련 정보 기본값 초기화
        webhookdata["pageurl"] = None
        webhookdata["pagetitle"] = None
        webhookdata["pageid"] = None
        webhookdata["parentid"] = None
        # 웹훅 엔티티가 페이지일 경우 추가 정보 처리
        if data["entity"]["type"] == "page":
            pageid = data["entity"]["id"]
            webhookdata["pageid"] = pageid
            if data["data"]["parent"]["type"] == "database":
                parentid = data["data"]["parent"]["id"]
                # 부모 데이터베이스 캐시 조회 + 추후 디스코드에 정보 전송을 위해 업데이트 플래그 설정
                res = await notionservice.get_notion_database(conn, parentid)
                if res:
                    await updatePage(conn, pageid, parentid)
            # 페이지 정보 가져와서 제목과 URL 파싱
            pagedata = await get_page_func(pageid, token)
            if pagedata:
                for item in pagedata["properties"]:
                    if pagedata["properties"][item].get("type") == "title":
                        if pagedata["properties"][item]["title"]:
                            webhookdata["pagetitle"] = pagedata["properties"][item][
                                "title"
                            ][0]["text"]["content"]
                webhookdata["pageurl"] = pagedata["url"]
    # webhookdata를 JSON 문자열로 직렬화
    if not webhookdata["pagetitle"]:
        return JSONResponse(content={"message": "Webhook received"})
    webhookdata = json.dumps(webhookdata)
    # 채널이 연결되어 있는지 확인 (없으면 에러)
    if server.webhook_channel_id is None:
        return JSONResponse(
            content={
                "status": "error",
                "message": "No channel linked"},
            status_code=400)
    # Discord bot 서버에 요청 전송 (notion webhook 전달)
    try:
        url = discordbot + DISCORD_APP_ROOT + f"/call/notionwebhook"
        await make_request(method="GET", url=url, params={"params": webhookdata})
        # TODO: 이것도 왜 GET 요청 보냄? 지금 API 설계가 이상함
    except Exception as e:
        # 디코 봇이 꺼져 있는 경우인데 그냥 무시
        pass
    return JSONResponse(content={"message": "Webhook received"})


# ======================================================================

page_cache = TTLCache(maxsize=100, ttl=60 * 60)  # 1 hour


async def get_page_func(
    pageid: str, token: str, forcereload: bool = False
) -> Optional[dict]:
    """
    Get the page information from Notion.
    """
    if not forcereload:
        cached = page_cache.get(pageid)
        if cached:
            return cached
    url = NOTION_API_URL + f"/pages/{pageid}"
    statuscode, response = await make_request(
        url=url, headers=notionHeaders(token), method="GET", internal=False
    )
    if statuscode != 200:
        print(
            f"get_page_func: {url} with headers {
                notionHeaders(token)} -> {statuscode}"
        )
        print(f"Response: {response}")
        return None
    page_cache[pageid] = response
    return response


user_cache = TTLCache(maxsize=100, ttl=12 * 60 * 60)


async def get_user_func(notionuserid: str, token: str):
    """
    Get the user information from Notion.
    """
    response = user_cache.get(notionuserid)
    if response:
        return response
    url = NOTION_API_URL + f"/users/{notionuserid}"
    statuscode, response = await make_request(
        url=url, headers=notionHeaders(token), method="GET", internal=False
    )
    if statuscode != 200:
        print(f"get_page_func: {url} -> {statuscode}")
        return None
    user_cache[notionuserid] = response
    return response


async def updatePage(conn, pageid: str, databaseid: str):
    """
    mark the page need to update
    """
    await notionservice.mark_update_notion_page(conn, pageid, databaseid)
    return JSONResponse(
        content={"status": "success", "message": "Page updated successfully"}
    )
