from time import time

from cachetools import TTLCache


class BiDirectionalTTLCache(TTLCache):
    def __init__(self, maxsize: int, ttl: int, timer=time):
        super().__init__(maxsize=maxsize, ttl=ttl, timer=timer)
        self._inverse = {}

    def __setitem__(self, key: int, value: int):
        # 기존 쌍이 있으면 제거
        if key in self:
            old_value = super().__getitem__(key)
            self._inverse.pop(old_value, None)

        if value in self._inverse:
            old_key = self._inverse[value]
            super().__delitem__(old_key)

        super().__setitem__(key, value)
        self._inverse[value] = key

    def __delitem__(self, key: int):
        if key in self:
            value = super().__getitem__(key)
            super().__delitem__(key)
            self._inverse.pop(value, None)

    def get_by_value(self, value: int) -> int | None:
        self.expire()
        return self._inverse.get(value)

    def popitem(self):
        # 캐시 만료 관리
        key, value = super().popitem()
        self._inverse.pop(value, None)
        return key, value
