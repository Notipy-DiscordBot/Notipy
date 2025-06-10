import asyncio
from functools import partial
from typing import Optional

from commons import *
from fastapi import Request
from interactions import *

fastapi: MyFunctions = None

webhookBase = SlashCommand(name=getname("webhook"))


class Webhook(Extension):
    bot: Client = None
    functions: MyFunctions = None

    def __init__(self, bot: Client, functions: MyFunctions):
        self.bot = bot
        self.functions = functions
        self.functions.set("notionwebhook", notionWebhook)

    def drop(self) -> None:
        """
        Drop the extension.
        """
        self.functions.remove("notionwebhook")
        super().drop()

    @webhookBase.subcommand(
        sub_cmd_name=getname("set"), sub_cmd_description=getdesc("set_webhook")
    )
    @localize()
    async def set_notion_webhook(self, ctx: SlashContext, _):
        """
        Set the Notion webhook.
        """
        channelid = int(ctx.channel.id)
        guildid = int(ctx.guild_id)
        status, response = await apirequest(
            f"/discord/{guildid}/webhookchannel", method="PUT", json=channelid
        )
        if status != 200:
            raise ValueError("Error in /discord/setwebhookchannel")
        await ctx.send(_("set_webhook_channel_success"), ephemeral=True)


colors = {
    "page.content_updated": 0x7F8C8D,
    "page.created": 0xE74C3C,
    "page.deleted": 0x2ECC71,
    "page.locked": 0x9B59B6,
    "page.moved": 0x34495E,
    "page.properties_updated": 0xF1C40F,
    "page.undeleted": 0x3498DB,
    "page.unlocked": 0x1ABC9C,
    "database.content_updated": 0xE67E22,
    "database.created": 0xFD79A8,
    "database.deleted": 0x2D3436,
    "database.moved": 0x8E44AD,
    "database.schema_updated": 0x16A085,
    "database.undeleted": 0xF39C12,
    "comment.created": 0x2980B9,
    "comment.deleted": 0xC0392B,
    "comment.updated": 0x27AE60,
}


async def notionWebhook(bot: Client, params: dict) -> None:
    """
    Notion webhook handler.
    """
    channelid = params["channelid"]
    channel = await bot.fetch_channel(channelid)
    guildid = int(channel.guild.id)
    if "verification_token" in params:
        await channel.send(
            f"Here is your verification token: ||{params["verification_token"]}||"
        )
        return
    locale = channel.guild.preferred_locale
    type_ = getlocale(params["type"], locale)
    embed = Embed(title=type_,
                  color=colors[params["type"]],
                  description=params["workspace_name"])
    if params["pageurl"] is not None:
        embed.url = params["pageurl"]
    if params["pagetitle"] is not None:
        embed.description = params["workspace_name"] + \
            " - " + params["pagetitle"]
    embed.set_author(name=str(params["author"]), icon_url=params["avatar_url"])
    if channel is None:
        return
    await channel.send(embeds=embed)
