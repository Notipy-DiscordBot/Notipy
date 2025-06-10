from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Sequence, Tuple

from caches import *
from db.models import *
from sqlalchemy import Row, RowMapping, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import selectinload

from .discordservice import get_discord_server, update_server_info_fields

notion_user_cache = get_notion_user_cache_service()
notion_page_cache = get_notion_page_cache_service()
notion_database_cache = get_notion_database_cache_service()
discord_server_cache = get_discord_server_cache_service()


async def set_notion_token(
    conn: AsyncSession, discordid: int, token: str
) -> Optional[ServerInfo]:
    server = await get_discord_server(conn, discordid)
    if server is None:
        return
    await update_server_info_fields(conn, server, notion_token=token)
    discord_server_cache.set(discordid, server)
    return server


async def get_notion_token(
        conn: AsyncSession,
        discordid: int) -> Optional[str]:
    server = discord_server_cache.get(discordid)
    if server:
        if server.notion_token:
            return server.notion_token
    server = await get_discord_server(conn, discordid)
    return server.notion_token


async def get_notion_database(
    conn: AsyncSession, databaseid: str, eager_load: bool = False
) -> Optional[NotionDatabase]:
    if not eager_load:
        notionlink = notion_database_cache.get(databaseid)
        if notionlink:
            return notionlink
    stmt = select(NotionDatabase).where(
        NotionDatabase.database_id == databaseid)
    if eager_load:
        stmt = stmt.options(
            selectinload(
                NotionDatabase.server), selectinload(
                NotionDatabase.pages))
    result = await conn.execute(stmt)
    notionlink = result.scalars().first()
    if notionlink is None:
        return None
    notion_database_cache.set(databaseid, notionlink)
    return notionlink


async def get_linked_notion_database(
    conn: AsyncSession, channelid: int, eager_load: bool = False
) -> Optional[NotionDatabase]:
    stmt = select(NotionDatabase).where(NotionDatabase.channel_id == channelid)
    if eager_load:
        stmt = stmt.options(
            selectinload(
                NotionDatabase.server), selectinload(
                NotionDatabase.pages))
    result = await conn.execute(stmt)
    notionlink = result.scalars().first()
    if notionlink:
        notion_database_cache.set(notionlink.database_id, notionlink)
    return notionlink


async def link_notion_database(
    conn: AsyncSession,
    discordid: int,
    databaseid: str,
    databasename: str,
    channelid: int,
) -> None:
    notionlink = NotionDatabase(
        server_id=discordid,
        database_id=databaseid,
        database_name=databasename,
        channel_id=channelid,
    )
    conn.add(notionlink)
    notion_database_cache.set(databaseid, notionlink)
    await conn.commit()


async def delete_notion_database(
    conn: AsyncSession, databaseid: str
) -> Optional[NotionDatabase]:
    """
    Delete a notion database from the database after retrieving it.
    :param conn: database connection
    :param databaseid: notion database id
    :return: the deleted NotionDatabase object (or None if not found)
    """
    db_obj = await get_notion_database(conn, databaseid, True)
    if db_obj is None:
        return None
    await conn.execute(
        delete(NotionDatabase).where(NotionDatabase.database_id == databaseid)
    )
    await conn.commit()
    notion_database_cache.delete(databaseid)
    return db_obj


async def set_notion_database_name(
    conn: AsyncSession, databaseid: str, name: str
) -> Optional[NotionDatabase]:
    """
    Set the name of a notion database.
    :param conn: database connection
    :param databaseid: notion database id
    :param name: new name for the database
    :return: updated NotionDatabase object
    """
    db_obj = await get_notion_database(conn, databaseid)
    if db_obj is None:
        return None
    await update_notion_database_fields(conn, db_obj, database_name=name)
    db_obj.database_name = name
    notion_database_cache.set(databaseid, db_obj)
    return db_obj


async def create_notion_page(
    conn: AsyncSession, pageid: str, databaseid: str
) -> NotionPages:
    notionpage = NotionPages(page_id=pageid, database_id=databaseid)
    conn.add(notionpage)
    notion_page_cache.set(pageid, notionpage)
    await conn.commit()
    return notionpage


async def get_notion_page(
    conn: AsyncSession, pageid: str, eager_load: bool = False
) -> Optional[NotionPages]:
    stmt = select(NotionPages).where(NotionPages.page_id == pageid)
    if eager_load:
        stmt = stmt.options(selectinload(NotionPages.database))
    result = await conn.execute(stmt)
    notionpage = result.scalars().first()
    if notionpage:
        notion_page_cache.set(pageid, notionpage)
    return notionpage


async def mark_update_notion_page(
    conn: AsyncSession, pageid: str, databaseid: str
) -> Optional[NotionPages]:
    notionpage = await get_notion_page(conn, pageid)
    if notionpage is None:
        notionpage = await create_notion_page(conn, pageid, databaseid)
    if notionpage.blocked:  # 운이 좋으면 캐시 선에서 작업이 끝남
        return None
    if notionpage.updated:
        return notionpage
    await update_notion_page_fields(conn, notionpage, updated=True)
    notionpage.updated = True
    notion_page_cache.set(pageid, notionpage)
    return notionpage


async def remove_notion_page(
        conn: AsyncSession,
        pageid: str) -> Optional[NotionPages]:
    """
    Remove a notion page from the database after retrieving it.
    :param conn: database connection
    :param pageid: notion page id
    :return: the deleted NotionPages object (or None if not found)
    """
    notionpage = await get_notion_page(conn, pageid)
    if notionpage is None:
        return None
    await conn.execute(delete(NotionPages).where(NotionPages.page_id == pageid))
    await conn.commit()
    notion_page_cache.delete(pageid)
    return notionpage


async def toggle_block_notion_page(
    conn: AsyncSession, pageid: str
) -> Optional[NotionPages]:
    notionpage = await get_notion_page(conn, pageid)
    if notionpage is None:
        return None
    blocked = not notionpage.blocked
    await update_notion_page_fields(conn, notionpage, blocked=blocked)
    notionpage.blocked = blocked
    notion_page_cache.set(pageid, notionpage)
    return notionpage


async def get_all_updated_pages(
    conn: AsyncSession,
) -> Sequence[tuple[NotionPages, str, int, str, list[str]]]:
    page_query = (
        select(
            NotionPages,
            NotionDatabase.database_id,
            NotionDatabase.channel_id,
            ServerInfo.server_id,
            ServerInfo.notion_token,
        ) .join(
            NotionDatabase,
            NotionPages.database_id == NotionDatabase.database_id) .join(
                ServerInfo,
                NotionDatabase.server_id == ServerInfo.server_id) .where(
                    NotionPages.updated,
            NotionPages.blocked == False))
    page_results = (await conn.execute(page_query)).all()

    server_ids = {row[3] for row in page_results}  # row[3] = server_id
    tag_query = select(NotionTags.server_id, NotionTags.tag).where(
        NotionTags.server_id.in_(server_ids)
    )
    tag_results = await conn.execute(tag_query)
    raw_tags = tag_results.all()

    tag_map = defaultdict(list)
    for server_id, tag in raw_tags:
        if len(tag_map[server_id]) < 3:
            tag_map[server_id].append(tag)

    output: list[tuple[NotionPages, str, int, str, list[str]]] = []
    for page, dbid, channel_id, server_id, token in page_results:
        output.append(
            (page,
             dbid,
             channel_id,
             token,
             tag_map.get(
                 server_id,
                 [])))

    return output


async def set_thread_id(
    conn: AsyncSession, pageid: str, threadid: int
) -> Optional[NotionPages]:
    notionpage = await get_notion_page(conn, pageid)
    if notionpage is None:
        return None
    await update_notion_page_fields(conn, notionpage, thread_id=threadid)
    notionpage.thread_id = threadid
    notion_page_cache.set(pageid, notionpage)
    return notionpage


async def get_threads(conn: AsyncSession, databaseid: str) -> Sequence[int]:
    query = select(NotionPages.thread_id).where(
        NotionPages.database_id == databaseid)
    result = await conn.execute(query)
    return result.scalars().all()


async def set_pages_updated(
    conn: AsyncSession, threadids: Sequence[int]
) -> Optional[Sequence[NotionPages]]:
    query = select(NotionPages).where(NotionPages.thread_id.in_(threadids))
    result = await conn.execute(query)
    notionpages = result.scalars().all()
    if not notionpages:
        return None
    for page in notionpages:
        page.updated = False
        notion_page_cache.set(page.page_id, page)
    await update_notion_page_bulk_fields(conn, threadids, updated=False)
    query = delete(NotionPages).where(NotionPages.thread_id is None)
    await conn.execute(query)
    await conn.commit()
    return notionpages


async def update_notion_page_fields(
    conn: AsyncSession, page: NotionPages, **kwargs
) -> None:
    stmt = (
        update(NotionPages).where(
            NotionPages.page_id == page.page_id).values(
            **kwargs))
    await conn.execute(stmt)
    await conn.commit()


async def update_notion_page_bulk_fields(
    conn: AsyncSession, threadids: Sequence[int], **kwargs
) -> None:
    stmt = (
        update(NotionPages).where(
            NotionPages.thread_id.in_(threadids)).values(
            **kwargs))
    await conn.execute(stmt)
    await conn.commit()


async def update_notion_database_fields(
    conn: AsyncSession, db: NotionDatabase, **kwargs
) -> None:
    stmt = (
        update(NotionDatabase)
        .where(NotionDatabase.database_id == db.database_id)
        .values(**kwargs)
    )
    await conn.execute(stmt)
    await conn.commit()
    notion_database_cache.set(db.database_id, db)
