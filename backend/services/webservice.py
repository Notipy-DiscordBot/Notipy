import secrets
from datetime import datetime, timedelta, timezone
from typing import Sequence

from db.models import Admin, Notification
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def notification_post(conn: AsyncSession, title: str, msg: str):
    """
    Post a notification for webpage
    :param conn: database connection
    :param title: title of the notification
    :param msg: message content of the notification
    """
    notification = Notification(title=title, content=msg)
    conn.add(notification)
    await conn.commit()
    return notification


async def get_notification(conn: AsyncSession) -> Sequence[Notification]:
    """
    Get all notifications for the webpage.
    :param conn: database connection
    :return: list of Notification objects
    """
    query = select(Notification).order_by(Notification.created_at.desc())
    result = await conn.execute(query)
    return result.scalars().all()


async def get_token(conn: AsyncSession) -> str:
    """
    Get the token for the webpage.
    :param conn: database connection
    :return: token string
    """
    # Assuming the token is stored in a specific table or configuration
    # This is a placeholder implementation
    query = select(Admin)
    result = await conn.execute(query)
    admin = result.scalars().first()
    now = datetime.now(timezone.utc)
    if not admin:
        # Create a new admin entry if it doesn't exist
        admin = Admin(token=secrets.token_urlsafe(32), created_at=now)
        conn.add(admin)
    elif not admin.token or admin.created_at.replace(
        tzinfo=timezone.utc
    ) < now - timedelta(hours=1):
        admin.token = secrets.token_urlsafe(32)
        admin.created_at = now
    else:
        return admin.token
    await conn.commit()
    return admin.token
