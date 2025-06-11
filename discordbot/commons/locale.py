import json
from functools import partial, wraps
from os import getenv, listdir
from os.path import abspath, dirname, isfile, join
from typing import Callable, Union

from interactions import (ComponentContext, LocalisedDesc, LocalisedName,
                          SlashContext)

from .localization import language_codes

locales = {}
default_locale = "en-US"  # 기본 로케일
used_keys = set()
_used_keys_cache = set()
_write_counter = 0
WRITE_EVERY = 20
USED_KEYS_LOG_PATH = "./used_translation_keys.json"

debug = getenv("DEBUG")

# 로케일 파일 로딩
wd = dirname(abspath(__file__))
for file in listdir(wd + "/localization"):
    if file.endswith(".json") and isfile(join(wd + "/localization", file)):
        with open(join(wd + "/localization", file), "r", encoding="utf-8") as f:
            locales[file[:-5]] = json.load(f)

def localize(server_only: bool = True):
    def decorator(func):
        @wraps(func)
        async def wrapped_func(
            self, ctx: Union[SlashContext, ComponentContext], *args, **kwargs
        ):
            if server_only and not ctx.guild:
                _ = localizator(ctx.locale)
                await ctx.send(_("server_only_error"), ephemeral=True)
                return None

            locale = ctx.locale
            if locale not in locales:
                locale = ctx.guild.preferred_locale if ctx.guild else default_locale
            return await func(self, ctx, localizator(locale), *args, **kwargs)

        return wrapped_func

    return decorator


def localizator(locale) -> Callable[[str], str]:
    return partial(getlocale, locale=locale)


def getlocale(key_: str, locale: str) -> str:
    used_keys.add(key_)

    try:
        with open(USED_KEYS_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted(used_keys), f, ensure_ascii=False, indent=2)
        # _write_counter = 0
    except Exception as e:
        print(f"⚠️ Failed to write used keys: {e}")

    if key_ in locales.get(locale, {}):
        return locales[locale][key_]
    if key_ in locales.get(default_locale, {}):
        return locales[default_locale][key_]
    return key_


def getname(name) -> LocalisedName:
    names = {}
    for locale in locales:
        if name in locales[locale]:
            names[language_codes[locale]] = locales[locale][name].lower().replace(" ", "_")
    if language_codes[default_locale] not in names:
        names[language_codes[default_locale]] = name
    return LocalisedName(**names)


def getdesc(name) -> LocalisedDesc:
    name += "_desc"
    descs = {}
    for locale in locales:
        if name in locales[locale]:
            descs[language_codes[locale]] = locales[locale][name]
    if language_codes[default_locale] not in descs:
        descs[language_codes[default_locale]] = name
    return LocalisedDesc(**descs)
