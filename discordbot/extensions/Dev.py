import asyncio

from commons import *
from interactions import *


class Dev(Extension):
    bot: Client = None

    def __init__(self, bot):
        self.bot = bot
        asyncio.create_task(self.async_init())

    async def async_init(self):
        pass

    @slash_command(
        name=getname("ping"), description=getdesc("ping"), scopes=[devserver]
    )
    @slash_option(
        name=getname("ping_opt"),
        description=getdesc("ping_opt"),
        required=False,
        opt_type=OptionType.BOOLEAN,
    )  # noqa
    @localize()
    async def hello(self, ctx: SlashContext, _):
        await ctx.send(_("pong"), ephemeral=True)

    @message_context_menu(name="공지")
    @check(is_dev)
    async def notice(self, ctx: ContextMenuContext):
        """
        Send a notice to the dev server
        :param ctx: Context of the message
        """
        content = ctx.target.content
        if not content:
            await ctx.send(_("메시지 내용이 없습니다."), ephemeral=True)
            return
        modal = Modal(
            ShortText(label="공지 제목", custom_id="notice_title", required=True),
            title="공지 작성",
        )
        await ctx.send_modal(modal)
        modal_response: ModalContext = await ctx.bot.wait_for_modal(modal, timeout=60)
        if modal_response is None:
            await ctx.send("모달 응답이 없습니다.", ephemeral=True)
            return
        title = modal_response.responses["notice_title"]
        json = {"title": title, "message": content}
        await apirequest("/discord/notification", method="POST", json=json)
        await ctx.send("공지 등록 완료!", ephemeral=True)

    @slash_command(name="view_token",
                   description="View the current token",
                   scopes=[devserver])
    @check(is_dev)
    async def view_token(self, ctx: SlashContext):
        """
        View the current token
        :param ctx: Context of the command
        """
        status, res = await apirequest("/web/token", method="GET")
        if status != 200:
            await ctx.send("token fetch failed", ephemeral=True)
            return
        token = res["token"]
        await ctx.send(f"Current token: ||`{token}`||", ephemeral=True)


def setup(bot, functions):
    Dev(bot)


def teardown():
    pass
