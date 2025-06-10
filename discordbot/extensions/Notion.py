import asyncio
import re
from datetime import datetime, timezone
from typing import Optional

from commons import *
from interactions import *
from interactions.api.events import Component

notionBase = SlashCommand(name=getname("notion"))
notionTokenGroup = notionBase.group(name=getname("notiontoken"))
notionTagGroup = notionBase.group(name=getname("notiontag"))
notiondbGroup = notionBase.group(name=getname("notiondb"))


def getNotionToken():
    """
    Decorator for injecting the Notion token (as a str) into a class method.\
    """

    def wrapper(func):
        @wraps(func)
        async def wrapped_func(
            self,
            ctx: SlashContext | ComponentContext,
            _: Callable[[str], str],
            *args,
            **kwargs,
        ):
            await ctx.defer(ephemeral=True)
            if not ctx.guild:
                # optional localized message
                raise ValueError(_("guild_only_command"))

            guildid = ctx.guild_id
            status, response = await apirequest(
                f"/discord/{guildid}/notion/token", method="GET"
            )

            if status != 200 or "token" not in response:
                await ctx.send(_("notion_token_not_found"), ephemeral=True)
                return None

            notion_token = response["token"]

            # `_`는 그대로 넘기기
            return await func(self, ctx, _, notion_token, *args, **kwargs)

        return wrapped_func

    return wrapper


async def getNotionDatabases(notion_token: str) -> Optional[list[dict]]:
    """
    Get the Notion databases.
    """
    status, response = await apirequest(
        "/notion/external/databases", json=notion_token, method="POST"
    )
    if status != 200:
        return None
    data = response["data"]
    data = data["results"]
    results = []
    for result in data:
        title = result["title"][0]["plain_text"]
        url = result["url"]
        id_ = result["id"]
        results.append({"title": title, "url": url, "id": id_})
    return results


class Notion(Extension):
    bot: Client = None
    regex_pattern = re.compile(r"togglepageblock_([a-f0-9\-]{32,36})")

    def __init__(self, bot):
        self.bot = bot
        self.update_notion_page.start()
        asyncio.create_task(self.async_init())

    async def async_init(self):
        """
        Async init function.
        """
        await self.update_notion_page()

    @notionTokenGroup.subcommand(sub_cmd_name=getname("set"),
                                 sub_cmd_description=getdesc("set_notion_token"))
    @check(is_moderator)
    @localize()
    async def set_notion_token(self, ctx: SlashContext, _):
        my_modal = Modal(
            ShortText(
                label="Notion API Token",
                placeholder=_("notion_token_placeholder"),
                required=True,
                custom_id="notion_token",
            ),
            title=_("set_notion_token"),
        )
        await ctx.send_modal(modal=my_modal)
        modalctx: ModalContext = await ctx.bot.wait_for_modal(my_modal)
        notion_token = modalctx.responses["notion_token"]
        status, response = await apirequest(
            f"/discord/{ctx.guild_id}/notion/token", method="PUT", json=notion_token
        )
        if status != 200:
            raise ValueError("Error in /notion/setnotiontoken")
        await modalctx.send(_("notion_token_set"), ephemeral=True)

    @notionTokenGroup.subcommand(
        sub_cmd_name=getname("remove"),
        sub_cmd_description=getdesc("remove_notion_token"),
    )
    @check(is_moderator)
    @localize()
    async def remove_notion_token(self, ctx: SlashContext, _):
        status, response = await apirequest(
            f"discord/{ctx.guild_id}/notion/token", method="PUT", json=None
        )
        if status != 200:
            raise ValueError(f"Error in /discord/{ctx.guild_id}/notion/token")
        await ctx.send(_("notion_token_removed"), ephemeral=True)

    @notiondbGroup.subcommand(sub_cmd_name=getname("view"),
                              sub_cmd_description=getdesc("view_notion_db"))
    @cooldown(Buckets.USER, 1, 10)
    @check(is_moderator)
    @localize()
    @getNotionToken()
    async def view_notion_databases(
            self,
            ctx: SlashContext,
            _,
            notion_token: str):
        """
        Test the Notion API.
        """
        results = await getNotionDatabases(notion_token)
        if results is None:
            await ctx.send(_("notion_api_error"), ephemeral=True)
            return
        embed = Embed(title=_("notion_api_results"), color=createRandomColor())
        for result in results:
            title = result["title"]
            url = result["url"]
            embed.add_field(name=title,
                            value=f"[{_('goto')}]({url})",
                            inline=True)
        await ctx.send(embed=embed, ephemeral=True)

    @notiondbGroup.subcommand(
        sub_cmd_name=getname("connect"),
        sub_cmd_description=getdesc("connect_notion_db"),
    )
    @cooldown(Buckets.USER, 1, 10)
    @check(is_moderator)
    @localize()
    @getNotionToken()
    async def connect_notion(self, ctx: SlashContext, _, notion_token: str):
        """
        Connect to a Notion database.
        """
        # 일단 채널을 고릅니다
        results = await getNotionDatabases(notion_token)
        channelselect = ChannelSelectMenu(
            channel_types=[ChannelType.GUILD_TEXT, ChannelType.GUILD_FORUM],
            placeholder=_("select_channel"),
        )
        message = await ctx.send(
            content=_("select_notion_channel"), components=channelselect, ephemeral=True
        )
        res = await wait_for_component_interaction(ctx, channelselect, message)
        if res is None:
            return
        usedctx, channel = res
        # 채널을 고른 후 notion db를 고릅니다
        dbselect = StringSelectMenu(
            *[
                StringSelectOption(label=result["title"], value=result["id"])
                for result in results
            ],
            placeholder=_("select_notion_db"),
        )
        await usedctx.edit_origin(content=_("select_notion_db"), components=dbselect)
        res = await wait_for_component_interaction(usedctx, dbselect, message)
        if res is None:
            return
        usedctx, databaseid = res
        # 이제 고른값들을 서버에 저장합니다
        await usedctx.defer(edit_origin=True)
        channelid = int(channel.id)
        guildid = int(ctx.guild_id)
        databasename = None
        for result in results:
            if result["id"] == databaseid:
                databasename = result["title"]
                break
        json = {
            "channelid": channelid,
            "databaseid": databaseid,
            "databasename": databasename,
            "serverid": guildid,
        }
        status, response = await apirequest(
            "/notion/database", json=json, method="POST"
        )
        # 서버 응답에 따라 메시지를 보냅니다
        if status == 400:
            await usedctx.edit_origin(content=_(response["message"]), components=[])
            return
        if status != 200:
            raise ValueError("Error in /notion/database")
        await usedctx.edit_origin(content=_("notion_db_linked"), components=[])

    @notiondbGroup.subcommand(
        sub_cmd_name=getname("disconnect"),
        sub_cmd_description=getdesc("disconnect_notion_db"),
    )
    @check(is_moderator)
    @localize()
    async def disconnect_notion(self, ctx: SlashContext, _):
        """
        Disconnect from a Notion database.
        """
        serverid = int(ctx.guild_id)
        status, response = await apirequest(
            f"/discord/{serverid}/notion/database", method="GET"
        )
        if status == 204:
            await ctx.send(_("notion_db_not_linked"), ephemeral=True)
            return
        elif status != 200:
            raise ValueError(f"Error In: /discord/{serverid}/notion/database")
        options = []
        for database in response["database"]:
            channelid = database["channel_id"]
            channel = await ctx.bot.fetch_channel(channelid)
            if channel is None:
                continue
            channelname = channel.name
            options.append(
                StringSelectOption(
                    label=channelname,
                    value=database["database_id"]))
        if not options:
            await ctx.send(_("notion_db_not_linked"), ephemeral=True)
            return
        dbselect = StringSelectMenu(*options, placeholder=_("select_channel"))
        message = await ctx.send(
            _("select_linked_notion_db_channel"), components=dbselect, ephemeral=True
        )
        res = await wait_for_component_interaction(ctx, dbselect, message)
        if not res:
            return
        usedctx, databaseid = res
        await usedctx.defer(edit_origin=True)
        status, response = await apirequest(
            f"/notion/database/{databaseid}", method="DELETE"
        )
        if status == 204:
            await usedctx.edit_origin(content=_("notion_db_not_linked"), components=[])
            return
        elif status != 200:
            raise ValueError(f"Error In: DELETE /notion/database/{databaseid}")
        threadids = response["data"]["threads"]
        channelid = response["data"]["channelid"]
        components = None
        if threadids:  # if there are threads, we need to delete them
            components = Button(
                style=ButtonStyle.RED,
                label=_("remove"),
                custom_id="remove_notion_db_channels",
            )
        message = await usedctx.edit_origin(
            content=_("notion_db_disconnected"), components=components
        )
        res = await wait_for_component_interaction(usedctx, components, message)
        if not res:
            return
        usedctx, _ = res
        await usedctx.defer(edit_origin=True)
        channel = await ctx.bot.fetch_channel(channelid)
        if not channel:
            return
        if isinstance(channel, GuildForum):
            for threadid in threadids:
                thread = await channel.fetch_post(threadid)
                if thread:
                    await thread.delete()
        else:
            for threadid in threadids:
                message = await channel.fetch_message(threadid)
                if message:
                    await message.delete()
        await usedctx.edit_origin(content=_("notion_db_disconnected"), components=[])

    @notiondbGroup.subcommand(sub_cmd_name=getname("list"),
                              sub_cmd_description=getdesc("list_notion_db"))
    @check(is_moderator)
    @localize()
    async def list_notion(self, ctx: SlashContext, _):
        """
        List the Notion databases.
        """
        serverid = int(ctx.guild_id)
        status, response = await apirequest(
            f"/discord/{serverid}/notion/database", method="GET"
        )
        if status == 204:
            await ctx.send(_("notion_db_not_linked"), ephemeral=True)
            return
        elif status != 200:
            raise ValueError(f"Error In: /discord/{serverid}/notion/database")
        embed = Embed(title=_("notion_db_list"), color=createRandomColor())
        for database in response["database"]:
            channelid = database["channel_id"]
            channel: GuildForum | GuildText = await ctx.bot.fetch_channel(channelid)
            if channel is None:
                continue
            embed.add_field(
                name=database["database_name"],
                value=channel.mention,
                inline=False)
        await ctx.send(embed=embed, ephemeral=True)

    @component_callback(regex_pattern)
    @check(is_moderator)
    @localize()
    async def toggle_block_notion_db(self, ctx: ComponentContext, _):
        match = self.regex_pattern.match(ctx.custom_id)
        if match:
            page_id = match.group(1)
            status, response = await apirequest(
                f"/notion/notionpage/{page_id}/toggleblock", method="PUT"
            )
            if status == 204:
                await ctx.send(_("notion_page_not_found"), ephemeral=True)
            if status != 200:
                raise ValueError(
                    f"Error in /notion/notionpage/{page_id}/toggleblock")
                return
            if response["data"]:  # the page is blocked
                button = Button(
                    style=ButtonStyle.PRIMARY,
                    label=_("notion_unblock_page"),
                    custom_id=f"togglepageblock_{page_id}",
                )
            else:  # the page is unblocked
                button = Button(
                    style=ButtonStyle.SECONDARY,
                    label=_("notion_block_page"),
                    custom_id=f"togglepageblock_{page_id}",
                )
            await ctx.edit_origin(components=button)

    @notionTagGroup.subcommand(sub_cmd_name=getname("set"),
                               sub_cmd_description=getdesc("set_notion_tag"))
    @check(is_moderator)
    @localize()
    async def set_notion_tag(self, ctx: SlashContext, _):
        """
        Set the Notion tag.
        """
        my_modal = Modal(
            ShortText(
                label="Notion Tag",
                placeholder=_("notion_tag_placeholder"),
                required=True,
                custom_id="notion_tag",
            ),
            title=_("set_notion_tag"),
        )
        await ctx.send_modal(modal=my_modal)
        modalctx: ModalContext = await ctx.bot.wait_for_modal(my_modal)
        notion_tag = modalctx.responses["notion_tag"]
        status, response = await apirequest(
            f"/discord/{ctx.guild_id}/notion/tag", method="POST", json=notion_tag
        )
        if status == 429:
            await modalctx.send(_(response["detail"]), ephemeral=True)
            return
        elif status != 200:
            raise ValueError("Error in /notion/setnotiontag")
        await modalctx.send(_("notion_tag_set"), ephemeral=True)

    @notionTagGroup.subcommand(sub_cmd_name=getname("remove"),
                               sub_cmd_description=getdesc("remove_notion_tag"))
    @check(is_moderator)
    @localize()
    async def remove_notion_tag(self, ctx: SlashContext, _):
        """
        Remove the Notion tag.
        """
        status, response = await apirequest(
            f"/discord/{ctx.guild_id}/notion/tag", method="GET"
        )
        if status != 200:
            raise ValueError("Error in /notion/removenotiontag")
        tags = response["tag"]
        options = []
        for tag in tags:
            tagname = tag["tag"]
            options.append(StringSelectOption(label=tagname, value=tagname))
        if not options:
            await ctx.send(_("notion_tag_not_set"), ephemeral=True)
            return
        tagselect = StringSelectMenu(
            *options, placeholder=_("select_notion_tag"))
        message = await ctx.send(
            _("select_notion_tag"), components=tagselect, ephemeral=True
        )
        res = await wait_for_component_interaction(ctx, tagselect, message)
        if not res:
            return
        usedctx, tagname = res
        await usedctx.defer(edit_origin=True)
        status, response = await apirequest(
            f"/discord/{ctx.guild_id}/notion/tag/{tagname}", method="DELETE"
        )
        if status != 200:
            raise ValueError("Error in /notion/removenotiontag")
        await usedctx.edit_origin(content=_("notion_tag_removed"), components=[])

    @Task.create(IntervalTrigger(minutes=5))
    async def update_notion_page(self):
        """
        Update the Notion page.
        """
        status, res = await apirequest("/notion/notionpage/updated", method="GET")
        if status == 204:
            return
        if status != 200:
            raise ValueError("Error in /notion/updated")
        if res["data"] is None:
            return
        success = []
        for result in res["data"]:
            status = result["status"]
            if not status:
                continue
            channelid = result["channelid"]
            channel = await self.bot.fetch_channel(channelid)
            if not channel:
                return  # TODO: delete subscription
            embed = Embed(title=result["pagetitle"], color=createRandomColor())
            embed.url = result["pageurl"]
            embed.set_footer(
                text="Updated: "
                + datetime.now(timezone.utc).strftime("%B %d, %Y, %I:%M %p")
            )
            for key, value in result["props"].items():
                if key == "title":
                    continue
                if isinstance(value, list):
                    value = ", ".join(value)
                if value is None or value.strip() == "":
                    value = getlocale(
                        "not_set", channel.guild.preferred_locale)
                embed.add_field(name=key, value=value, inline=False)
            try:
                if isinstance(channel, GuildForum):
                    res = await self.send_to_forum(channel, result, embed)
                else:
                    res = await self.send_to_channel(channel, result, embed)
                if res:
                    success.append(res)
            except Exception as e:
                self.bot.logger.warning("Error in Notion webhook: %s", e)
        if success:
            await apirequest("/notion/notionpage/updated", method="POST", json=success)

    async def send_to_forum(
            self,
            channel: GuildForum,
            pagedata: dict,
            embed: Embed):
        thread: GuildForumPost = None
        new = True
        threadid = pagedata.get("threadid")
        targettags = pagedata.get("tags")
        applytag = []
        tags = channel.available_tags
        if threadid:
            thread = await channel.fetch_post(threadid)
        if thread:
            new = False
            await thread.edit(name=pagedata["pagetitle"])
            # fetch the message to edit
            message = await thread.fetch_message(threadid)
            await message.edit(embed=embed)
        else:
            thread = await channel.create_post(
                name=pagedata["pagetitle"], content="", embed=embed
            )
        for targettag in targettags[:5]:  # limit to 5 tags, Discord API limit
            tag = next((t for t in tags if t.name == targettag), None)
            if not tag:
                tag = await channel.create_tag(targettag)
            applytag.append(tag)
            await thread.edit(applied_tags=applytag)
        if new:
            await apirequest(
                f"/notion/notionpage/{pagedata['pageid']}/threadid",
                method="PUT",
                json=thread.id,
            )
            await self.send_block_button(thread, pagedata["pageid"])
        return thread.id

    async def send_to_channel(
            self,
            channel: GuildText,
            pagedata: dict,
            embed: Embed):
        message = None
        messageid = pagedata.get("threadid")
        guild = channel.guild
        if messageid:
            message = await guild.fetch_thread(messageid)
        if message:
            message = await channel.fetch_message(messageid)
            await message.edit(embed=embed)
            return None
        message = await channel.send(embed=embed)
        channel = await message.create_thread(name=pagedata["pagetitle"])
        await apirequest(
            f"/notion/notionpage/{pagedata['pageid']}/threadid",
            method="PUT",
            json=message.id,
        )
        await self.send_block_button(channel, pagedata["pageid"])
        return message.id

    async def send_block_button(
            self,
            channel: GuildForumPost | GuildText,
            pageid: str):
        """
        Send the block button to the channel.
        """
        local = channel.guild.preferred_locale
        content = getlocale("notion_block_page_msg", local)
        button = Button(
            style=ButtonStyle.SECONDARY,
            label=getlocale("notion_block_page", local),
            custom_id=f"togglepageblock_{pageid}",
        )
        message = await channel.send(content, components=button)
        await message.pin()


def setup(bot, functions):
    Notion(bot)


def teardown():
    pass
