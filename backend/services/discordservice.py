from datetime import datetime, timedelta
from typing import Optional

from caches import get_discord_server_cache_service
from db.models import NotionTags, ServerInfo
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

discordServerCache = get_discord_server_cache_service()


async def update_server_info_fields(
    conn: AsyncSession, server: ServerInfo, **kwargs
) -> None:
    """
    Update specified fields of a ServerInfo row in the database.

    :param conn: database connection
    :param server: ServerInfo object (used for identifying the row)
    :param kwargs: fields to update (e.g., mod_id=..., notion_token=...)
    """
    kwargs["updated"] = datetime.now()
    stmt = (
        update(ServerInfo)
        .where(ServerInfo.server_id == server.server_id)
        .values(**kwargs)
    )
    await conn.execute(stmt)
    await conn.commit()
    discordServerCache.set(server.server_id, server)


async def mark_and_clean_discord_servers(
    conn: AsyncSession, active_server_ids: list[int]
) -> None:
    """
    - Mark given servers as updated (set updated = now)
    - Delete all other servers that haven't been updated in 24h
    - Remove deleted servers from cache
    """
    if active_server_ids:
        # Step 1: 갱신 대상 서버 업데이트
        update_stmt = (
            update(ServerInfo)
            .where(ServerInfo.server_id.in_(active_server_ids))
            .values(updated=func.now())  # DB 기준 시간
        )
        await conn.execute(update_stmt)
    # Step 2: 삭제 기준 시간 계산
    cutoff = datetime.now() - timedelta(days=1)
    # Step 3: 삭제 대상 서버 ID 미리 조회해서 캐시 정리
    expired_stmt = select(
        ServerInfo.server_id).where(
        ServerInfo.updated < cutoff)
    expired_result = await conn.execute(expired_stmt)
    expired_ids = expired_result.scalars().all()
    for server_id in expired_ids:
        discordServerCache.delete(server_id)
    # Step 4: DB에서 실제 삭제
    delete_stmt = delete(ServerInfo).where(ServerInfo.updated < cutoff)
    await conn.execute(delete_stmt)
    await conn.commit()


async def remove_discord_server(
    conn: AsyncSession, server_id: int
) -> None | ServerInfo:
    query = select(ServerInfo).where(ServerInfo.server_id == server_id)
    server = await conn.execute(query)
    server = server.scalars().first()
    if not server:
        return None
    await conn.delete(server)
    await conn.commit()
    discordServerCache.delete(server_id)
    return server


async def create_discord_server(
        conn: AsyncSession,
        server_id: int) -> ServerInfo:
    """
    this adds a discord server to the database
    :param conn: database connection
    :param server_id: discord server id
    :return: server info object
    """
    query = select(ServerInfo).where(ServerInfo.server_id == server_id)
    server = await conn.execute(query)
    server = server.scalars().first()
    if not server:
        server = ServerInfo(server_id=server_id)
        conn.add(server)
        await conn.commit()
        await conn.refresh(server)
        discordServerCache.set(server_id, server)
    return server


async def get_discord_server(
    conn: AsyncSession, server_id: int, eager_load: bool = False
) -> ServerInfo:
    server = discordServerCache.get(server_id)
    if server and not eager_load:
        return server
    # 1. 쿼리 작성
    stmt = select(ServerInfo).where(ServerInfo.server_id == server_id)
    if eager_load:
        stmt = stmt.options(
            selectinload(ServerInfo.notion_databases),
            selectinload(ServerInfo.notion_tags),
        )
    # 2. DB에서 조회
    result = await conn.execute(stmt)
    server = result.scalar_one_or_none()
    # 3. 없으면 생성
    if not server:
        server = ServerInfo(server_id=server_id)
        conn.add(server)
        await conn.commit()
    # 4. 캐시에 저장 후 리턴
    discordServerCache.set(server_id, server)
    return server


async def set_mod_role(
    conn: AsyncSession, server_id: int, mod_id: int
) -> Optional[ServerInfo]:
    """
    this sets the mod role for a discord server
    :param conn: database connection
    :param server_id: discord server id
    :param mod_id: discord role id
    :return: server info object
    """
    server = await get_discord_server(conn, server_id)
    server.mod_id = mod_id
    await update_server_info_fields(conn, server, mod_id=mod_id)
    return server


async def get_mod_role(conn: AsyncSession, server_id: int) -> Optional[int]:
    """
    this gets the mod role for a discord server
    :param conn: database connection
    :param server_id: discord server id
    :return: discord role id
    """
    server = await get_discord_server(conn, server_id)
    return server.mod_id


async def set_webhook_channel(
    conn: AsyncSession, server_id: int, channel_id: int
) -> Optional[ServerInfo]:
    """
    this sets the webhook channel for a discord server
    :param conn: database connection
    :param server_id: discord server id
    :param channel_id: discord channel id
    :return: server info object
    """
    server = await get_discord_server(conn, server_id)
    server.webhook_channel_id = channel_id
    await update_server_info_fields(conn, server, webhook_channel_id=channel_id)
    return server


async def get_notion_tag(conn, server_id: int) -> Optional[list[NotionTags]]:
    query = select(NotionTags).where(NotionTags.server_id == server_id)
    result = await conn.execute(query)
    return result.scalars().all()


async def add_notion_tag(conn, server_id: int, tag: str) -> NotionTags:
    """
    Appends a new Notion tag for a Discord server.
    """
    notion_tag = NotionTags(server_id=server_id, tag=tag)
    conn.add(notion_tag)
    await conn.commit()
    return notion_tag


async def remove_notion_tag(conn, server_id: int, tag: str) -> None:
    """
    Removes a Notion tag for a Discord server.
    """
    query = select(NotionTags).where(
        NotionTags.server_id == server_id, NotionTags.tag == tag
    )
    result = await conn.execute(query)
    notion_tag = result.scalars().first()
    if notion_tag:
        await conn.delete(notion_tag)
        await conn.commit()


async def get_notion_database(conn, serverid: int):
    """
    this gets the notion database for a discord server
    :param conn: database connection
    :param serverid: discord server id
    :return: notion database id
    """
    server = await get_discord_server(conn, serverid, True)
    if not server:
        return None
    return server.notion_databases
