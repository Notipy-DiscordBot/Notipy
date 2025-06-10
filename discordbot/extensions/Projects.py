import asyncio
import re
from functools import partial
from typing import Sequence, Union

from commons import *
from interactions import *
from interactions.ext.paginators import Paginator

projectBase = SlashCommand(name=getname("projects"))
projectMemberGroup = projectBase.group(name=getname("member"))

manage_project_member_regex = re.compile(r"manage_project_member_select_(\d+)")
add_project_member_regex = re.compile(r"add_project_member_(\d+)")
remove_project_member_regex = re.compile(r"remove_project_member_(\d+)")


def parse_int_safe(val: str) -> Optional[int]:
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def parse_json_list_safe(val: str) -> Optional[list[str]]:
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list) and all(isinstance(i, str)
                                            for i in parsed):
            return parsed
    except json.JSONDecodeError:
        pass
    return None


def parse_comma_list(val: str) -> list[str]:
    # "AI, Web,Mobile" -> ["AI", "Web", "Mobile"]
    return [item.strip() for item in val.split(",") if item.strip()]


def validate_project_field(
        field: str, value: str) -> Union[str, int, list[str], None]:
    """
    field 이름에 따라 적절한 타입으로 파싱 및 유효성 검증 후 반환.
    유효하지 않으면 None 반환
    """
    match field:
        case "team_size":
            return parse_int_safe(value)
        case "category" | "core_features" | "tech_stack":
            return parse_comma_list(value)
        case "complexity" | "database" | "platform":
            return value.strip() if value.strip() else None
        case _:
            return None  # 처리 대상이 아닌 경우


async def editproject(ctx: ComponentContext, paginator: Paginator, _):
    """
    Callback function to edit a project.
    This function is called when a user selects a project from the paginator.
    """
    userid = ctx.author.id
    projectid, projectname = get_project_from_paginator(paginator)
    # 항목 선택 UI
    select_menu = StringSelectMenu(
        StringSelectOption(label=_("category"), value="category"),
        StringSelectOption(label=_("team_size"), value="team_size"),
        StringSelectOption(label=_("core_features"), value="core_features"),
        StringSelectOption(label=_("tech_stack"), value="tech_stack"),
        StringSelectOption(label=_("complexity"), value="complexity"),
        StringSelectOption(label=_("database"), value="database"),
        StringSelectOption(label=_("platform"), value="platform"),
        StringSelectOption(label=_("notifications"), value="notifications"),
        StringSelectOption(label=_("map_integration"), value="map_integration"),
        StringSelectOption(label=_("auth_required"), value="auth_required"),
        custom_id="select_edit_field",
        placeholder=_("select_edit_field_placeholder"),
    )
    msg = await ctx.send(
        _("select_edit_field_prompt"), components=[select_menu], ephemeral=True
    )
    res = await wait_for_component_interaction(ctx, select_menu, msg, timeout=60)
    if not res:
        return None
    select_ctx, field = res
    parsed = None
    if field in {
        "category",
        "team_size",
        "core_features",
        "tech_stack",
        "complexity",
        "database",
        "platform",
    }:
        # Modal 요청
        modal = Modal(
            ParagraphText(label=_(field), custom_id=field, required=True),
            title=_("edit_project_field_title"),
        )
        await select_ctx.send_modal(modal)
        modalctx = await ctx.bot.wait_for_modal(modal)
        await modalctx.defer(edit_origin=True)

        value = modalctx.responses[field]
        parsed = validate_project_field(field, value)
        if parsed is None:
            return await modalctx.send(_(f"{field}_invalid_value"), ephemeral=True)
        # DB 업데이트
    else:
        modalctx = select_ctx
        await modalctx.defer(edit_origin=True)
    status, response = await apirequest(
        f"/llm/projects/{userid}/{projectid}", method="PUT", json={field: parsed}
    )
    if status == 204:
        return await modalctx.send(_(f"project_not_found"), ephemeral=True)
    if status != 200:
        raise ValueError(f"Error in /llm/projects/{userid}/{projectid}")
    await modalctx.send(
        _(f"{field}_update_success"), ephemeral=True, components=[], delete_after=10
    )
    return None


async def send_project_paginator(
    ctx: SlashContext, _, content: str = "", callback: callable = None
):
    """
    Send a paginator with project embeds.
    :param ctx: SlashContext
    :param _: Localized string function
    :param content: Content to send with the paginator
    :param callback: Optional callback function to handle project selection
    """
    status, response = await apirequest(
        f"/llm/projects/{ctx.author_id}/server/{ctx.guild_id}"
    )
    if status == 204:
        await ctx.send(_("no_projects_found"), ephemeral=True)
        return
    elif status != 200:
        raise ValueError(f"Error in /llm/projects/{ctx.author_id}")
    projects = response["projects"]
    embeds = [create_project_embed(project, _) for project in projects]
    paginator = Paginator.create_from_embeds(ctx.bot, *embeds, timeout=160)
    paginator.show_select_menu = True
    paginator.show_callback_button = True if callback else False
    paginator.callback = (
        partial(callback, paginator=paginator, _=_) if callback else None
    )
    await paginator.send(ctx, content=_(content), ephemeral=True)


def create_project_embed(project, _):
    if len(project["description"]) > 1000:
        project["description"] = project["description"][:1000] + "..."
    embed = Embed(
        title=project["name"],
        description=project["description"],
        color=createRandomColor(),
    )
    embed.add_field(
        name=_("core_features"),
        value=", ".join(
            project["core_features"]),
        inline=False)
    embed.add_field(
        name=_("tech_stack"),
        value=", ".join(
            project["tech_stack"]),
        inline=False)
    embed.add_field(
        name=_("project_id"),
        value=project["project_id"],
        inline=True)
    embed.add_field(name=_("category"), value=project["category"], inline=True)
    embed.add_field(
        name=_("team_size"),
        value=project["team_size"],
        inline=True)
    embed.add_field(
        name=_("complexity"),
        value=project["complexity"],
        inline=True)
    embed.add_field(name=_("database"), value=project["database"], inline=True)
    embed.add_field(name=_("platform"), value=project["platform"], inline=True)
    embed.add_field(
        name=_("notifications"), value=project["notifications"], inline=True
    )
    embed.add_field(
        name=_("map_integration"),
        value=project["map_integration"],
        inline=True)
    embed.add_field(
        name=_("auth_required"), value=project["auth_required"], inline=True
    )
    return embed


def get_project_from_paginator(paginator: Paginator) -> Tuple[str, str]:
    """
    Get the project data from the paginator.
    :param paginator: Paginator object
    :return: Tuple containing project ID and project name
    """
    project = paginator.to_dict()["embeds"][0]
    # project = project[paginator.page_index]  # 이거 없는데 왜 되는건지 모르겠음
    # print(f"Project data from paginator: {project}")
    projectid = project["fields"][2]["value"]  # Project ID 위치
    projectname = project["title"]  # Project 이름 위치
    return projectid, projectname


async def manage_project_member(
        ctx: ComponentContext,
        paginator: Paginator,
        _):
    """
    Callback function to manage project members.
    This function is called when a user selects a project from the paginator.
    """
    projectid, projectname = get_project_from_paginator(paginator)
    options = []
    options.append(
        StringSelectOption(
            label=_("view_project_member"),
            value=f"view_project_member"))
    options.append(
        StringSelectOption(
            label=_("add_project_member"),
            value=f"add_project_member"))
    options.append(
        StringSelectOption(
            label=_("remove_project_member"), value=f"remove_project_member"
        )
    )
    component = StringSelectMenu(
        *options,
        placeholder=_("select_project_member_action"),
        custom_id=f"manage_project_member_select_{projectid}",
    )
    await ctx.send(
        content=_("select_project_member_action_desc").format(projectname),
        components=[component],
        ephemeral=True,
    )


async def set_project_member(ctx: ComponentContext, paginator: Paginator, _):
    """
    Callback for assigning project members to roles automatically.
    This function is triggered after selecting a project from the paginator.
    """
    await ctx.defer(ephemeral=True)
    projectid, projectname = get_project_from_paginator(paginator)

    # FastAPI API 호출
    status, response = await apirequest(
        f"/llm/project/{ctx.author.id}/{projectid}/assign/auto", method="POST"
    )
    if status == 204:
        return await ctx.send(
            _("project_not_found_or_no_roles_or_members"), ephemeral=True
        )
    elif status != 200:
        raise ValueError(
            f"Error in /llm/project/{ctx.author.id}/{projectid}/assign/auto"
        )
    data = response.get("data", {})
    if not data:
        return await ctx.send(_("no_assignments_result"), ephemeral=True)
    embed = Embed(
        title=_("role_assignment_result_title"),
        color=createRandomColor())
    for rolename, discord_ids in data.items():
        mentions = ", ".join(f"<@{uid}>" for uid in discord_ids)
        embed.add_field(
            name=rolename,
            value=mentions or "(none)",
            inline=False)
    return await ctx.send(
        _("project_members_assigned_success"), embed=embed, ephemeral=True
    )


class Projects(Extension):
    bot: Client = None

    def __init__(self, bot):
        self.bot = bot

    @projectBase.subcommand(sub_cmd_name=getname("list"),
                            sub_cmd_description=getdesc("projects_list"))
    @check(is_moderator)
    @localize()
    async def list_projects(self, ctx: SlashContext, _):
        """
        List all projects.
        """
        await send_project_paginator(ctx, _, "list_projects_desc", editproject)

    @projectBase.subcommand(sub_cmd_name=getname("view"),
                            sub_cmd_description=getdesc("projects_view"))
    @localize()
    async def view_project(self, ctx: SlashContext, _):
        """
        view projects I am involved in.
        """
        authorid = int(ctx.author_id)
        guildid = int(ctx.guild_id)
        status, repsonse = await apirequest(
            f"/llm/project/participating/{authorid}/{guildid}"
        )
        if status == 204:
            await ctx.send(_("no_projects_found"), ephemeral=True)
            return
        elif status != 200:
            raise ValueError(
                f"Error in /llm/project/participating/{authorid}/{guildid}"
            )
        projects = repsonse["projects"]
        if not projects:
            await ctx.send(_("no_projects_found"), ephemeral=True)
            return
        embeds = [create_project_embed(project, _) for project in projects]
        paginator = Paginator.create_from_embeds(ctx.bot, *embeds, timeout=160)
        paginator.show_select_menu = True
        await paginator.send(ctx, content=_("view_projects_content"), ephemeral=True)

    @projectBase.subcommand(sub_cmd_name=getname("create"),
                            sub_cmd_description=getdesc("projects_create"))
    @cooldown(Buckets.USER, 2, 400)
    @check(is_moderator)
    @localize()
    async def create_project(self, ctx: SlashContext, _):
        """
        Create a new project.
        """
        if not ctx.guild:
            await ctx.send(_("project_create_server_only"), ephemeral=True)
            return
        modal = Modal(
            ShortText(
                label=_("project_create_title"),
                value=_("project_create_title"),
                max_length=255,
                custom_id="title",
            ),
            ParagraphText(
                label=_("project_create_description"),
                value=_("project_create_description"),
                custom_id="description",
            ),
            title=_("project_create_title"),
        )
        await ctx.send_modal(modal)
        modealctx: ModalContext = await ctx.bot.wait_for_modal(modal)
        await modealctx.defer(ephemeral=True)
        name = modealctx.responses["title"]
        description = modealctx.responses["description"]
        data = {
            "name": name,
            "description": description,
            "serverid": int(
                ctx.guild_id)}
        status, response = await apirequest(
            f"/llm/projects/{ctx.author_id}", method="POST", json=data
        )
        if status != 200:
            raise ValueError(f"Error in /llm/projects/{ctx.author_id}")
        proj = response["data"]
        embed = create_project_embed(proj, _)
        await modealctx.send(_("project_created_success"), embed=embed, ephemeral=True)

    @projectBase.subcommand(sub_cmd_name=getname("remove"),
                            sub_cmd_description=getdesc("projects_remove"))
    @check(is_moderator)
    @localize()
    async def remove_project(self, ctx: SlashContext, _):
        """
        Remove a project.
        """
        status, response = await apirequest(
            f"/llm/projects/{ctx.author_id}/server/{ctx.guild_id}"
        )
        if status != 200:
            raise ValueError(f"Error in /llm/projects/{ctx.author_id}")
        if not response:
            await ctx.send(_("no_projects_found"), ephemeral=True)
            return
        options = [
            StringSelectOption(label=project["name"], value=project["project_id"])
            for project in response["projects"]
        ]
        select = StringSelectMenu(
            *options,
            placeholder=_("select_project_to_remove"),
            custom_id="remove_project_select",
        )
        await ctx.send(
            _("select_project_to_remove_desc"), components=[select], ephemeral=True
        )

    @component_callback("remove_project_select")
    @localize()
    async def remove_project_select(self, ctx: ComponentContext, _):
        """
        Handle the project removal selection.
        """
        project_id = ctx.values[0]
        status, response = await apirequest(
            f"/llm/projects/{ctx.author_id}/{project_id}", method="DELETE"
        )
        if status != 200:
            raise ValueError(
                f"Error in /llm/projects/{ctx.author_id}/{project_id}")
        await ctx.edit_origin(content=_("project_removed_success"), components=[])

    @projectMemberGroup.subcommand(
        sub_cmd_name=getname("manage"),
        sub_cmd_description=getdesc("manage_project_member"),
    )
    @check(is_moderator)
    @localize()
    async def add_project_member(self, ctx: SlashContext, _):
        """
        Add a member to a project.
        """
        await send_project_paginator(
            ctx, _, "select_project_to_manage_member", manage_project_member
        )

    @component_callback(manage_project_member_regex)
    @localize()
    async def manage_project_member_callback(self, ctx: ComponentContext, _):
        """
        Handle the project member management selection.
        This function is called when a user selects an action for project members.
        """
        match = manage_project_member_regex.match(ctx.custom_id)
        if not match:
            return None
        projectid = match.group(1)
        action = ctx.values[0]
        members = None
        if action in ["remove_project_member", "view_project_member"]:
            status, response = await apirequest(
                f"/llm/project/{ctx.author.id}/{projectid}/member"
            )
            if status == 204:
                return await ctx.send(
                    _("project_not_found_or_no_member"), ephemeral=True
                )
            if status != 200:
                raise ValueError(
                    f"Error in /llm/project/{ctx.author.id}/{projectid}/member"
                )
            members = response["members"]

        if action == "add_project_member":
            component = UserSelectMenu(
                placeholder=_("select_member_to_add"),
                custom_id=f"add_project_member_{projectid}",
            )
            await ctx.send(
                _("select_member_to_add_desc"), components=[component], ephemeral=True
            )
        elif action == "remove_project_member":
            options = []
            for member in members:
                discord_id = member["discordid"]
                mem = await ctx.guild.fetch_member(discord_id)
                if not mem:
                    continue
                githubid = member["githubid"]
                options.append(
                    StringSelectOption(
                        label=mem.display_name,
                        value=str(githubid)))
            component = StringSelectMenu(
                *[options],
                placeholder=_("select_member_to_remove"),
                custom_id=f"remove_project_member_{projectid}",
            )
            await ctx.send(
                _("select_member_to_remove_desc"),
                components=[component],
                ephemeral=True,
            )
        elif action == "view_project_member":
            embed = Embed(
                title=_("project_members_list"),
                color=createRandomColor())
            for member in members:
                discord_id = member["discordid"]
                mem = await ctx.guild.fetch_member(discord_id)
                if not mem:
                    continue
                embed.add_field(
                    name=mem.display_name,
                    value=f"GitHub ID: {member['githubid']}",
                    inline=False,
                )
            await ctx.send(embed=embed, ephemeral=True)
        return None

    @component_callback(add_project_member_regex)
    @localize()
    async def add_project_member_callback(self, ctx: ComponentContext, _):
        """
        Handle the project member addition selection.
        This function is called when a user selects a project to add a member.
        """
        await ctx.defer(ephemeral=True)
        match = add_project_member_regex.match(ctx.custom_id)
        if not match:
            return None
        projectid = match.group(1)
        member: Member = ctx.values[0]
        if member.bot:
            return await ctx.send(_("cannot_add_bot_to_project"), ephemeral=True)
        status, response = await apirequest(
            f"/llm/project/{ctx.author.id}/{projectid}/member",
            method="POST",
            json=member.id,
        )
        if status == 204:
            return await ctx.send(_("project_not_found"), ephemeral=True)
        elif status == 409:
            return await ctx.send(_("project_member_already_exists"), ephemeral=True)
        elif status == 400:
            return await ctx.send(_("user_no_github"), ephemeral=True)
        elif status != 200:
            raise ValueError(
                f"Error in /llm/project/{ctx.author.id}/{projectid}/member"
            )
        return await ctx.send(_("project_member_added"), ephemeral=True, delete_after=5)

    @component_callback(remove_project_member_regex)
    @localize()
    async def remove_project_member_callback(self, ctx: ComponentContext, _):
        """
        Handle the project member removal selection.
        This function is called when a user selects a member to remove from a project.
        """
        await ctx.defer(ephemeral=True)
        match = remove_project_member_regex.match(ctx.custom_id)
        if not match:
            return None
        projectid = match.group(1)
        githubid = ctx.values[0]
        status, response = await apirequest(
            f"/llm/project/{ctx.author.id}/{projectid}/member/{githubid}",
            method="DELETE",
        )
        if status == 204:
            return await ctx.send(_("project_not_found_or_no_member"), ephemeral=True)
        if status != 200:
            raise ValueError(
                f"Error in /llm/project/{ctx.author.id}/{projectid}/member/{githubid}"
            )
        return await ctx.send(
            _("project_member_removed"), ephemeral=True, delete_after=5
        )

    @projectMemberGroup.subcommand(sub_cmd_name=getname("set"),
                                   sub_cmd_description=getdesc("set_project_member"))
    @check(is_moderator)
    @localize()
    async def set_project_member_trigger(self, ctx: SlashContext, _):
        """
        Show the list of projects and trigger auto role assignment after selection.
        """
        await send_project_paginator(
            ctx, _, "select_project_to_set_member", callback=set_project_member
        )


def setup(bot, functions):
    Projects(bot)
