import asyncio
import os
import re

from commons import *
from interactions import *

oauth2_url = os.environ["DISCORD_OAUTH2_URL"]

githubBase = SlashCommand(
    name=getname("github"),
    description=getdesc("github"))


def llmbutton(_):
    return Button(
        style=ButtonStyle.PRIMARY,
        label=_("llm_analyze_do"),
        custom_id=f"llm_github_analyze",
    )


def togglegitshow(_):
    return Button(
        style=ButtonStyle.PRIMARY,
        label=_("toggle_git_show"),
        custom_id="toggle_git_show",
    )


class User(Extension):
    bot: Client = None

    def __init__(self, bot):
        self.bot = bot
        asyncio.create_task(self.async_init())

    async def async_init(self):
        pass

    @githubBase.subcommand(
        sub_cmd_name=getname("gitlink"), sub_cmd_description=getdesc("gitlink")
    )
    @UserOption(required=False)
    @localize()
    async def gitlink(self, ctx: SlashContext, _, user: Member = None):
        gitbuttons = []
        if user:
            discordid = int(user.id)
            params = {
                "discordid": discordid,
                "other": 1,
                "serverid": ctx.guild_id}
            status, response = await apirequest(f"/user/get", params=params)
            if status == 204:
                await ctx.send(_("not_linked_github_other"), ephemeral=True)
                return
            elif status == 403:
                await ctx.send(_("not_allowed_other"), ephemeral=True)
                return
            elif status != 200:
                raise ValueError("Error in /user/get")
        else:
            discordid = int(ctx.author.id)
            status, response = await apirequest(f"/user/get?discordid={discordid}")
            gitbuttons = [
                Button(
                    style=ButtonStyle.URL,
                    label=_("link_github_button"),
                    url=oauth2_url),
                Button(
                    style=ButtonStyle.PRIMARY,
                    label=_("check_github_linked_button"),
                    custom_id="check_github_linked",
                ),
            ]
            if status == 204:  # No content which means user not found, create user
                await ctx.send(_("link_github"), ephemeral=True, components=gitbuttons)
                return
            if status != 200:
                raise ValueError("Error in /user/get")
        if response.get("github") is not None:
            embed = None
            button = togglegitshow(_)
            github = response["github"]
            repos = response["repos"]
            mainurl = githuburl + "/" + github["github_login"]
            if github["primary_languages"]:
                embed = create_git_embed(github, repos, _)
            else:
                button = llmbutton(_)
            msg = _("already_linked_github") + "\n" + mainurl
            await ctx.send(msg, ephemeral=True, embed=embed, components=button)
            return
        await ctx.send(_("link_github"), ephemeral=True, components=gitbuttons)

    @component_callback("check_github_linked")
    @localize()
    async def check_github_linked(self, ctx: ComponentContext, _):
        discordid = int(ctx.author.id)
        status, response = await apirequest(f"/user/get?discordid={discordid}")
        if status == 204:
            await ctx.send(_("not_linked_github"), ephemeral=True)
            return
        if status != 200:
            raise ValueError("Error in /user/get")
        github = response.get("github")
        if not github:
            await ctx.send(_("not_linked_github"), ephemeral=True)
            return
        mainurl = githuburl + "/" + github["github_login"]
        await ctx.edit_origin(
            content=_("success_linked_github") + "\n" + mainurl,
            components=[llmbutton(_)],
        )

    @component_callback("llm_github_analyze")
    @cooldown(Buckets.USER, 1, 300)  # 5 minutes cooldown
    @localize()
    async def llm_github_analyze_callback(self, ctx: ComponentContext, _):
        await ctx.defer(edit_origin=True)
        discordid = int(ctx.author.id)
        status, response = await apirequest(f"/llm/git/{discordid}", method="POST")
        if status == 204:
            await ctx.send(_("not_linked_github"), ephemeral=True)
            return
        if status != 200:
            raise ValueError("Error in /llm/git")
        data = response["data"]
        embed = create_git_embed(data, None, _)
        await ctx.edit_origin(
            content=_("llm_github_analyze_content"),
            embed=embed,
            components=togglegitshow(_),
        )

    @component_callback("toggle_git_show")
    @localize()
    async def toggle_git_show(self, ctx: ComponentContext, _):
        """
        Toggle the visibility of GitHub repositories in the embed.
        """
        discordid = int(ctx.author.id)
        status, reponse = await apirequest(
            f"/user/github/{discordid}/toggle", method="PUT", json=int(ctx.guild_id)
        )
        if status == 204:
            await ctx.send(_("not_linked_github"), ephemeral=True)
            return
        if status != 200:
            raise ValueError("Error in /user/github/toggle")
        data = reponse["data"]
        if data:
            await ctx.send(_("git_show_enabled"), ephemeral=True)
        else:
            await ctx.send(_("git_show_disabled"), ephemeral=True)


def create_git_embed(data, repos, _):
    """
    Create an embed for GitHub user data.
    """
    embed = Embed(title=_("llm_analyze_res"), color=createRandomColor())
    embed.add_field(
        _("primary_languages"),
        ", ".join(
            data["primary_languages"]),
        inline=True)
    embed.add_field(
        _("experience_years"),
        data["experience_years"],
        inline=True)
    embed.add_field(_("total_stars"), data["total_stars"], inline=True)
    embed.add_field(_("public_repos"), data["public_repos"], inline=True)
    embed.add_field(_("total_forks"), data["total_forks"], inline=True)
    if repos is None:
        embed.add_field(_("top_repos"), _("repo_not_analyzed"), inline=False)
    else:
        for repo in repos:
            value = f"[보러가기]({repo['url']})\n\n"
            value += repo["description"] if repo["description"] else _(
                "no_description")
            if len(repo["description"]) > 800:
                value = repo["description"][:800] + "..."
            name = f"{repo['name']} - {repo['stars']}⭐ - {repo['forks']}🍴"
            embed.add_field(name, value, inline=False)
    embed.set_footer(
        text=_("profile_created_at")
        + ": "
        + data["profile_created_at"]
        + "\n"
        + _("last_active_date")
        + ": "
        + data["last_active_date"]
    )
    # embed.add_field(_("profile_created_at"), data["profile_created_at"], inline=True)
    # embed.add_field(_("last_active_date"), data["last_active_date"], inline=True)
    return embed


def setup(bot, functions):
    User(bot)


def teardown():
    pass
