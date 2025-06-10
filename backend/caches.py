from typing import Any, Generic, TypeVar

from cachetools import TTLCache
from db.models import NotionDatabase, NotionPages, ServerInfo

K = TypeVar("K")
V = TypeVar("V")


class BaseTTLCacheService(Generic[K, V]):
    def __init__(self, ttl_seconds: int = 3 * 60 * 60, maxsize: int = 100):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)

    def get(self, key: K) -> V | None:
        return self.cache.get(key)

    def set(self, key: K, value: V) -> None:
        self.cache[key] = value

    def delete(self, key: K) -> None:
        if key in self.cache:
            del self.cache[key]

    def getAll(self) -> TTLCache[Any, Any]:
        return self.cache


# 각각의 캐시 서비스 정의
class NotionUserCacheService(BaseTTLCacheService[str, dict]):
    pass


class NotionPageCacheService(BaseTTLCacheService[str, NotionPages]):
    pass


class DiscordServerCacheService(BaseTTLCacheService[int, ServerInfo]):
    pass


class NotionDatabaseCacheService(BaseTTLCacheService[str, NotionDatabase]):
    pass


_notion_user_cache = NotionUserCacheService(ttl_seconds=12 * 60 * 60)  # 12시간
_notion_page_cache = NotionPageCacheService(12 * 60 * 60)  # 12시간
_discord_server_cache = DiscordServerCacheService()
_notion_database_cache = NotionDatabaseCacheService(ttl_seconds=12 * 60 * 60)


def get_notion_user_cache_service() -> NotionUserCacheService:
    return _notion_user_cache


def get_notion_page_cache_service() -> NotionPageCacheService:
    return _notion_page_cache


def get_discord_server_cache_service() -> DiscordServerCacheService:
    return _discord_server_cache


def get_notion_database_cache_service() -> NotionDatabaseCacheService:
    return _notion_database_cache
