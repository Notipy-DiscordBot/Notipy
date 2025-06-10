import asyncio
import re

from commons import *
from interactions import *
from interactions.api.events import GuildJoin, GuildLeft, MessageCreate

dmCache = BiDirectionalTTLCache(maxsize=100, ttl=60 * 60 * 24)  # 1 day cache
blockedUser = TTLCache(maxsize=100, ttl=60 * 60 * 24)
# {user_id: forum_thread_id}

settingsBase = SlashCommand(name=getname("settings"))
modroleGroup = settingsBase.group(name=getname("modrole"))
blockuserregex = re.compile(r"^blockuserdm_(\d+)$")


class Misc(Extension):
    bot: Client = None
    ownerdm = None
    emoji = None
    supportchannel = None

    def __init__(self, bot):
        self.bot = bot
        asyncio.create_task(self.async_init())

    async def async_init(self):
        """
        on ready, update all servers, and remove servers that are not in the bot's guilds
        """
        guilds = self.bot.guilds
        guilids = [int(guild.id) for guild in guilds]
        await apirequest(f"/discord/clean", json=guilids, method="POST")
        self.ownerdm = await self.bot.owner.fetch_dm(force=True)
        self.emoji = PartialEmoji.from_str(":white_check_mark:")
        if supportchannelid:
            self.supportchannel = await self.bot.fetch_channel(supportchannelid)

    @listen(MessageCreate)
    async def on_message(self, event: MessageCreate):
        if event.message.author.bot:
            return
        if self.supportchannel is None:
            return
        match event.message.channel.type:
            case ChannelType.GUILD_PUBLIC_THREAD:
                if event.message.channel.parent_id != self.supportchannel.id:
                    return
                await self.forum_message(event)
            case ChannelType.DM:
                await self.dm_message(event)

    async def forum_message(self, event: MessageCreate):
        """
        send channel from dm to support discord forum channel
        """
        print(dmCache.items())
        message = event.message
        channel = message.channel
        channelid = int(channel.id)
        authorid = dmCache.get_by_value(channelid)
        author = None
        if not authorid:  # forumthread id가 없으면
            params = {"channelid": channelid}
            status, res = await apirequest("/user/forumthread/bychannel", params=params)
            if status != 200 and status != 204:
                raise ValueError(
                    f"Error in /user/forumthread/bychannel with params {params}")
            authorid = res.get("userid")
        if not authorid:  # authorid가 없으면
            await channel.send("This channel is not linked to a user.")
            return
        author = await self.bot.fetch_user(authorid)
        if not author:
            await apirequest("/user/forumthread/{authorid}", method="DELETE")
            await channel.send("User not found.")
            return
        dmchannel = await author.fetch_dm()
        if not dmchannel:  # dm 채널이 없으면
            await apirequest("/user/forumthread/{authorid}", method="DELETE")
            await channel.send("User not found.")
            return
        dmCache[authorid] = channelid  # cache에 저장
        try:
            if message.content != "":
                await dmchannel.send(message.content)
            if message.attachments:
                for attachment in message.attachments:
                    await dmchannel.send(attachment.url)
            await message.add_reaction(self.emoji)
        except Exception as e:
            await channel.send(
                f"Failed to send message to DM: {e}\n Deleting forum thread."
            )
            await apirequest("/user/forumthread/{authorid}", method="DELETE")
            return

    async def dm_message(self, event: MessageCreate):
        """
        send channel from dm to support discord dm channel
        """
        global dmCache
        message = event.message
        author = message.author
        authorid = int(author.id)
        # forumthread id 가져오기
        forumthreadid = dmCache.get(authorid)
        forumthread = None
        if not forumthreadid:  # forumthreadid가 없으면
            params = {"userid": authorid}
            status, res = await apirequest("/user/forumthread", params=params)
            if status != 200 and status != 204:
                raise ValueError(
                    f"Error in /user/forumthread with params {params}")
            forumthreadid = res["channel"]
        # 여기까지 왔는데 forumthread id가 없으면 새로 생성해야 하는거
        if forumthreadid:
            forumthread = await self.supportchannel.fetch_post(
                forumthreadid
            )  # forumthreadid로 가져오기, 만일 없으면 None
        if not forumthread:  # forumthread 가 None 이다: 없거나 삭제된 경우
            name = f"DM: {
                author.display_name}#{
                author.discriminator} ({authorid})"
            content = f"DM from {
                author.mention} ({authorid})\nUse the button below to toggle block for the user."
            component = Button(
                style=ButtonStyle.SECONDARY,
                label="Toggle Block User",
                custom_id=f"blockuserdm_{authorid}",
            )
            forumthread = await self.supportchannel.create_post(
                name=name, content=content, components=[component]
            )
            dmCache[authorid] = int(forumthread.id)
            await apirequest(
                f"/user/forumthread/{authorid}/channelid",
                method="PUT",
                json=int(forumthread.id),
            )
        # await forumthread.edit(locked=True)
        try:
            if message.content != "":
                await forumthread.send(message.content)
            if message.attachments:
                for attachment in message.attachments:
                    await forumthread.send(attachment.url)
            await message.add_reaction(self.emoji)
        except Exception as e:
            await forumthread.send(f"Failed to send message to forum thread.")
            await apirequest(f"/user/forumthread/{authorid}", method="DELETE")
            return

    @component_callback(blockuserregex)
    @check(is_moderator)
    async def block_user_dm(self, ctx: ComponentContext, _):
        """
        Block user from sending dm to the bot.
        """
        userid = ctx.custom_id
        userid = int(userid.split("_")[-1])
        status, response = await apirequest(
            f"/user/forumthread/{userid}/block", method="PUT"
        )
        if status != 200:
            raise ValueError(f"Error in /user/forumthread/{userid}/block")
        if response.get("blocked") is True:
            await ctx.send("User Blocked", ephemeral=True)
        else:
            await ctx.send(_("User Unblocked"), ephemeral=True)

    @slash_command(name=getname("create_ticket"),
                   description=getdesc("create_ticket"))
    @check(is_moderator)
    @localize(True)
    async def create_ticket(self, ctx: SlashContext, _):
        """
        Create a ticket for the user.
        """
        modal = Modal(
            ParagraphText(
                label=_("create_ticket_modal_label"),
                required=True,
                custom_id="content"),
            ShortText(
                label=_("create_ticket_modal_shorttext_label"),
                required=True,
                custom_id="label",
            ),
            title=_("create_ticket_modal_title"),
        )
        await ctx.send_modal(modal)
        modal_ctx: ModalContext = await ctx.bot.wait_for_modal(modal)
        if modal_ctx is None:
            await ctx.send(_("modal_timeout"), ephemeral=True)
            return
        content = modal_ctx.responses["content"]
        label = modal_ctx.responses["label"]
        button = Button(
            style=ButtonStyle.PRIMARY,
            label=label,
            emoji="📤",
            custom_id=f"open_ticket")
        try:
            await ctx.channel.send(content, components=[button])
        except Exception as e:
            await modal_ctx.send(_("ticket_create_fail"), ephemeral=True)
        await modal_ctx.send(_("ticket_created"), ephemeral=True)

    @component_callback("open_ticket")
    @localize(True)
    async def open_ticket(self, ctx: SlashContext, _):
        """
        Open a ticket for the user.
        """
        status, res = await apirequest(f"/discord/{ctx.guild_id}/modrole")
        if status == 204:
            await ctx.send(_("ticket_create_fail_no_modrole"), ephemeral=True)
            return
        elif status != 200:
            raise ValueError(f"Error in /discord/{ctx.guild_id}/modrole")
        modrole = res["modrole"]
        modrole = await ctx.guild.fetch_role(modrole)
        if not modrole:
            await ctx.send(_("ticket_create_fail_no_modrole"), ephemeral=True)
            return
        category = ctx.channel.category
        if category is None:
            await ctx.send(_("ticket_create_fail_no_category"), ephemeral=True)
            return
        allow_overrides = (
            Permissions.VIEW_CHANNEL
            | Permissions.SEND_MESSAGES
            | Permissions.EMBED_LINKS
            | Permissions.ATTACH_FILES
            | Permissions.ADD_REACTIONS
        )
        bot_overrides = allow_overrides | Permissions.MANAGE_CHANNELS
        permission_overwrites = []
        try:
            for role in ctx.guild.roles:
                if (Permissions.VIEW_CHANNEL in ctx.channel.permissions_for(
                        role) and role != modrole):
                    permission_overwrites.append(
                        PermissionOverwrite(
                            id=role.id,
                            type=OverwriteType.ROLE,
                            deny=Permissions.VIEW_CHANNEL,
                        )
                    )
            permission_overwrites.append(
                PermissionOverwrite(
                    id=ctx.guild.default_role.id,
                    type=OverwriteType.ROLE,
                    deny=Permissions.VIEW_CHANNEL,
                )
            )
            permission_overwrites.append(
                PermissionOverwrite(
                    id=modrole.id,
                    type=OverwriteType.ROLE,
                    allow=allow_overrides))
            permission_overwrites.append(
                PermissionOverwrite(
                    id=ctx.author.id,
                    type=OverwriteType.MEMBER,
                    allow=allow_overrides))
            permission_overwrites.append(
                PermissionOverwrite(
                    id=self.bot.user.id,
                    type=OverwriteType.MEMBER,
                    allow=bot_overrides))
            channel = await category.create_text_channel(
                f"ticket-{str(ctx.author.id)[6:]}",
                permission_overwrites=permission_overwrites,
            )
            msg = ctx.author.mention + \
                _("ticket_create_success_msg") + channel.mention
            await ctx.send(msg, ephemeral=True)
            await channel.send(ctx.author.mention + _("ticket_created_channel"))
        except Exception as e:
            self.bot.logger.error(f"Failed to create ticket: {e}")
            await ctx.send(_("ticket_create_fail"), ephemeral=True)
            return

    @listen(GuildJoin, delay_until_ready=True)
    async def on_guild_join(self, guild: GuildJoin):
        if not self.bot.is_ready:
            return
        guildname = guild.guild.name
        guildid = guild.guild_id
        await apirequest(f"/discord/{guildid}", method="POST")
        await self.ownerdm.send(f"bot invited: {guildname}")

    @listen(GuildLeft, delay_until_ready=True)
    async def on_guild_left(self, guild: GuildLeft):
        guildname = guild.guild.name
        guildid = guild.guild_id
        await apirequest(f"/discord/{guildid}", method="DELETE")
        await self.ownerdm.send(f"bot removed: {guildname}")

    @modroleGroup.subcommand(
        sub_cmd_name=getname("set"), sub_cmd_description=getdesc("set_modrole")
    )
    @check(is_moderator)
    @localize()
    @roleOption()
    async def set_modrole(self, ctx: SlashContext, _, role):
        """
        Set the moderator role for the server.
        """
        guildid = int(ctx.guild_id)
        roleid = int(role.id)
        status, response = await apirequest(
            endpoint=f"/discord/{guildid}/modrole", method="PUT", json=roleid
        )
        if status != 200:
            raise ValueError(f"Error in /discord/{guildid}/modrole")
        await ctx.send(_("set_modrole_success"), ephemeral=True)

    @settingsBase.subcommand(sub_cmd_name=getname("view"),
                             sub_cmd_description=getdesc("view_settings"))
    @check(is_moderator)
    @localize()
    async def view_settings(self, ctx: SlashContext, _):
        """
        View the settings for the server.
        """
        guild = ctx.guild
        guildid = int(ctx.guild_id)
        status, response = await apirequest(
            f"/discord/{guildid}", params={"eager_load": 1}
        )
        if status != 200:
            raise ValueError(f"Error in /discord/{guildid}")
        if response["server"] is None:
            await ctx.send(_("no_settings"), ephemeral=True)
            return
        server = response["server"]
        mod = server["mod_id"]
        embed = Embed(title=_("settings_embed_title"), color=0x00FF00)
        if mod is None:
            mod = _("not_set")
        else:
            mod = await guild.fetch_role(mod)
            if mod is None:
                mod = _("none_role")
            else:
                mod = f"<@&{mod.id}>"
        embed.add_field(name=_("modrole"), value=mod, inline=True)
        webhookchannel = server["webhook_channel_id"]
        if webhookchannel is None:
            webhookchannel = _("not_set")
        else:
            webhookchannel = await guild.fetch_channel(webhookchannel)
            if webhookchannel is None:
                webhookchannel = _("none_channel")
            else:
                webhookchannel = webhookchannel.mention
        embed.add_field(
            name=_("webhook_channel"),
            value=webhookchannel,
            inline=True)
        notiontoken = server["notion_token"]
        if notiontoken is None:
            notiontoken = _("not_set")
        else:
            notiontoken = _("setted")
        embed.add_field(name=_("notiontoken"), value=notiontoken, inline=True)
        notion_tags = server["notion_tags"]
        tags = []
        for tag in notion_tags:
            tags.append(tag["tag"])
        if not tags:
            tags = [_("not_set")]
        else:
            tags = ", ".join(tags)
        embed.add_field(name=_("notiontag"), value=tags, inline=True)
        notion_databases = server["notion_databases"]
        databases = []
        for database in notion_databases:
            channel = database["channel_id"]
            channel = await guild.fetch_channel(channel)
            if channel is None:
                channel = _("none_channel")
            else:
                channel = channel.mention
            msg = f"{database['database_name']} → {channel}"
            databases.append(msg)
        if not databases:
            databases = [_("not_set")]
        else:
            databases = "\n".join(databases)
        embed.add_field(
            name=_("notion_databases"),
            value=databases,
            inline=False)
        await ctx.send(embeds=embed, ephemeral=True)

    @slash_command(name=getname("help"), description=getdesc("help"))
    @localize(True)
    async def send_help(self, ctx: SlashContext, _):
        """Send common command list."""
        embed = Embed(title=_("help_title"), color=0x5865F2)
        embed.description = _("help_description")
        await ctx.send(embeds=embed, ephemeral=True)


def setup(bot, functions):
    Misc(bot)
