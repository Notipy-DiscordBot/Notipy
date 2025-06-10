from datetime import datetime, timedelta
from typing import Any, Coroutine, Optional, Sequence

from db.models import DMchannel, Github, Notion, Repository, ShowGithub, User
from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession


class Tokens:
    def __init__(self, access_token: str, refresh_token: str, expires_in: int):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in


async def get_user(
    conn: AsyncSession, discordid: int
) -> tuple[User, Github, Notion] | None:
    """
    Get user by discord id
    :param conn: database connection
    :param discordid: discord id of user
    :return: user object, github object and notion object
    """
    query = (
        select(User, Github, Notion)
        .outerjoin(Github, User.discord_id == Github.discord_id)
        .outerjoin(Notion, User.discord_id == Notion.discord_id)
        .where(User.discord_id == discordid)
    )
    result = await conn.execute(query)
    result = result.all()
    if len(result) < 1:
        return None
    return result[0]


async def delete_user(conn: AsyncSession, discordid: int) -> bool:
    """
    Delete user by discord id
    :param conn: database connection
    :param discordid: discord id of user
    :return: True if deleted, False if not found
    """
    query = select(User).where(User.discord_id == discordid)
    user = await conn.execute(query)
    user = user.scalars().first()
    if not user:
        return False
    await conn.delete(user)
    await conn.commit()
    return True


async def delete_git(conn: AsyncSession, discordid: int) -> bool:
    """
    Delete github user by discord id
    :param conn: database connection
    :param discordid: discord id of user
    :return: True if deleted, False if not found
    """
    query = select(Github).where(Github.discord_id == discordid)
    github = await conn.execute(query)
    github = github.scalars().first()
    if not github:
        return False
    await conn.delete(github)
    await conn.commit()
    return True


async def delete_notion(conn: AsyncSession, discordid: int) -> bool:
    """
    Delete notion user by discord id
    :param conn: database connection
    :param discordid: discord id of user
    :return: True if deleted, False if not found
    """
    query = select(Notion).where(Notion.discord_id == discordid)
    notion = await conn.execute(query)
    notion = notion.scalars().first()
    if not notion:
        return False
    await conn.delete(notion)
    await conn.commit()
    return True


async def unlink_user(
        conn: AsyncSession,
        discordid: int,
        accountname: str) -> bool:
    """
    Unlink user by discord id, github id or notion id
    :param conn: database connection
    :param user: user object containing discordid, githubid or notionid
    :param accountname: name of the account to unlink (github or notion or both)
    :return: True if unlinked, False if not found
    """
    if accountname == "github":
        return await delete_git(conn, discordid)
    elif accountname == "notion":
        return await delete_notion(conn, discordid)
    elif accountname == "both":
        await delete_git(conn, discordid)
        await delete_notion(conn, discordid)
        return True
    else:
        return False


async def create_user(conn: AsyncSession, discordid: int) -> User:
    """
    Create user
    :param conn: database connection
    :param userdata: user object containing discordid, githubid or notionid
    :return: user object
    """
    user = User(discord_id=discordid)
    conn.add(user)
    await conn.commit()
    return user


async def link_github(
    conn: AsyncSession, discordid: int, githubid: int, gitlogin: str
) -> Github:
    """
    Link github user by discord id
    :param conn: database connection
    :param discordid: discord id of user
    :param githubid: github id of user
    :param gitlogin: github login of user
    :return: github object
    """
    query = select(Github).where(Github.discord_id == discordid)
    result = await conn.execute(query)
    github = result.scalars().first()
    if not github:
        github = Github(
            discord_id=discordid,
            github_id=githubid,
            github_login=gitlogin)
        conn.add(github)
    else:
        github.github_id = githubid
        github.github_login = gitlogin
    await conn.commit()
    return github


async def link_notion(
    conn: AsyncSession, discordid: int, notionid: int, notionlogin: str
) -> Notion | None:
    """
    Link notion user by discord id
    :param conn: database connection
    :param discordid: discord id of user
    :param notionid: notion id of user
    :param notionlogin: notion login of user
    :return: notion object
    """
    query = select(Notion).where(Notion.discord_id == discordid)
    result = await conn.execute(query)
    notion = result.scalars().first()
    if not notion:
        notion = Notion(
            discord_id=discordid, notion_id=notionid, notion_login=notionlogin
        )
        conn.add(notion)
    else:
        notion.notion_id = notionid
        notion.notion_login = notionlogin
    await conn.commit()
    return notion


async def setTokens(
        conn: AsyncSession,
        discordid: int,
        tokens: Tokens) -> User | None:
    """
    Set tokens for user
    :param conn: database connection
    :param discordid: discord id of user
    :param tokens: tokens object containing access_token, refresh_token and expires_in
    :return: user object
    """
    query = select(User).where(User.discord_id == discordid)
    result = await conn.execute(query)
    user = result.scalars().first()
    if not user:
        user = await create_user(conn, discordid)
    user.access_token = tokens.access_token
    user.refresh_token = tokens.refresh_token
    user.token_expires = datetime.now() + timedelta(seconds=tokens.expires_in)
    await conn.commit()
    return user


async def get_user_by_token(
        conn: AsyncSession,
        access_token: str) -> User | None:
    """
    Get user by access token
    :param conn: database connection
    :param access_token: access token of user
    :return: user object or None if not found
    """
    query = select(User).where(User.access_token == access_token)
    result = await conn.execute(query)
    return result.scalars().first()


async def update_github(conn: AsyncSession, github: Github) -> Github:
    """
    Update github user
    :param conn: database connection
    :param github: github object
    :return: None
    """
    github = await conn.merge(github)
    await conn.commit()
    return github


async def get_forum_channel(conn: AsyncSession, userid: int) -> DMchannel:
    """
    Get the forum channel for a user.
    :param conn: Database connection
    :param userid: Discord ID of the user
    :return: Forum channel ID or None if not found
    """
    query = select(DMchannel).where(DMchannel.user_id == userid)
    result = await conn.execute(query)
    dm_channel = result.scalars().first()
    if not dm_channel:
        new_dm_channel = DMchannel(user_id=userid)
        conn.add(new_dm_channel)
        await conn.commit()
        dm_channel = new_dm_channel
    return dm_channel


async def toggle_block_forum_channel(
        conn: AsyncSession,
        userid: int) -> DMchannel:
    """
    Block the forum channel for a user.
    :param conn: Database connection
    :param userid: Discord ID of the user
    """
    forumchannel = await get_forum_channel(conn, userid)
    forumchannel.block = not forumchannel.block
    await conn.commit()
    return forumchannel


async def get_forum_thread_by_channel(
    conn: AsyncSession, channelid: int
) -> Optional[DMchannel]:
    """
    Get the forum thread by channel ID.
    :param conn: Database connection
    :param channelid: Channel ID of the forum thread
    :return: Forum thread object or None if not found
    """
    query = select(DMchannel).where(DMchannel.channel_id == channelid)
    result = await conn.execute(query)
    return result.scalars().first()


async def delete_forum_thread(conn: AsyncSession, userid: int) -> bool:
    """
    Delete the forum thread for a user.
    :param conn: Database connection
    :param userid: Discord ID of the user
    :return: True if deleted, False if not found
    """
    query = select(DMchannel).where(DMchannel.user_id == userid)
    result = await conn.execute(query)
    forumthread = result.scalars().first()
    if not forumthread:
        return False
    await conn.delete(forumthread)
    await conn.commit()
    return True


async def set_forum_thread_channel(
    conn: AsyncSession, userid: int, channelid: int
) -> DMchannel:
    """
    Set the forum thread channel for a user.
    :param conn: Database connection
    :param userid: Discord ID of the user
    :param channelid: Channel ID to set for the forum thread
    :return: Updated forum thread object
    """
    forumthread = await get_forum_channel(conn, userid)
    forumthread.channel_id = channelid
    await conn.commit()
    return forumthread


async def get_repositories(
    conn: AsyncSession, github_id: int
) -> Sequence[Row[Repository]]:
    """
    Get all repositories for a GitHub user.
    :param conn: Database connection
    :param github_id: GitHub ID of the user
    :return: List of repositories
    """
    query = select(Repository).where(Repository.user_id == github_id)
    result = await conn.execute(query)
    return result.scalars().all()


async def get_git_show(
    conn: AsyncSession, discord_id: int, serverid: int
) -> Optional[bool]:
    """
    Get the GitHub show status for a Discord server.
    :param conn: Database connection
    :param discord_id: Discord ID of the server
    :return: True if GitHub show is enabled, False if disabled, None if not found
    """
    query = (
        select(ShowGithub)
        .where(ShowGithub.server_id == serverid)
        .where(ShowGithub.user_id == discord_id)
    )
    result = await conn.execute(query)
    show_github = result.scalars().first()
    if show_github is None:
        return None
    return show_github.show


async def toggle_github_show(
    conn: AsyncSession, serverid: int, discord_id: int
) -> ShowGithub:
    """
    Toggle the GitHub show status for a Discord server.
    :param conn: Database connection
    :param serverid: Server ID of the Discord server
    :param discord_id: Discord ID of the server
    :return: Updated ShowGithub object
    """
    query = (
        select(ShowGithub)
        .where(ShowGithub.server_id == serverid)
        .where(ShowGithub.user_id == discord_id)
    )
    result = await conn.execute(query)
    show_github = result.scalars().first()
    if not show_github:
        show_github = ShowGithub(
            server_id=serverid,
            user_id=discord_id,
            show=True)
        conn.add(show_github)
    else:
        show_github.show = not show_github.show
    await conn.commit()
    return show_github
