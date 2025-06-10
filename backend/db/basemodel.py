from datetime import date, datetime, time

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def todict(self, exclude=None, datetime_format="%Y-%m-%d %H:%M:%S"):
        exclude = exclude or []
        result = {}
        for c in inspect(self).mapper.column_attrs:
            if c.key in exclude:
                continue
            value = getattr(self, c.key)
            if isinstance(value, (datetime, date, time)):
                value = value.strftime(datetime_format)
            result[c.key] = value
        return result
