from datetime import datetime, timedelta
from typing import Any, Coroutine, Dict, List, Optional, Sequence, Tuple

from db.models import *
from sqlalchemy import Row, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def create_project(conn: AsyncSession, project: Project) -> Project:
    """
    Save project to database
    :param conn: database connection
    :param project: project object
    :return: None
    """
    conn.add(project)
    await conn.commit()
    await conn.refresh(project)
    return project


async def delete_project(
        conn: AsyncSession,
        owner_id: int,
        project_id: int) -> bool:
    """
    Delete project by id
    :param conn: database connection
    :param owner_id: discord id of user
    :param project_id: project id
    :return: True if deleted, False if not found
    """
    query = select(Project).where(
        Project.project_id == project_id, Project.owner_id == owner_id
    )
    result = await conn.execute(query)
    project = result.scalars().first()
    if not project:
        return False
    await conn.delete(project)
    await conn.commit()
    return True


async def set_projects(
    conn: AsyncSession, project_id: int, updates: Dict[str, Any]
) -> Project:
    """
    Update the fields of a project dynamically based on the provided updates dict.

    :param conn: Async database session
    :param project_id: ID of the project to update
    :param updates: Dict of key-value pairs to update
    :return: The updated Project object
    """
    # 먼저 해당 프로젝트가 존재하는지 확인
    result = await conn.execute(select(Project).where(Project.project_id == project_id))
    project: Project = result.scalar_one_or_none()
    if project is None:
        raise ValueError(f"Project with id {project_id} not found")
    # 업데이트 가능 필드 목록
    updatable_fields = {
        "name",
        "description",
        "category",
        "team_size",
        "core_features",
        "tech_stack",
        "complexity",
        "database",
        "platform",
        "notifications",
        "map_integration",
        "auth_required",
    }
    # 불리언 토글 대상 필드
    boolean_fields = {"notifications", "map_integration", "auth_required"}
    for key, value in updates.items():
        if key not in updatable_fields:
            continue
        if key in boolean_fields and value is None:
            current_value = getattr(project, key)
            if current_value is not None:
                setattr(project, key, not current_value)
        else:
            setattr(project, key, value)
    await conn.commit()
    await conn.refresh(project)
    return project


async def get_projects_by_owner(
    conn: AsyncSession, discordid: int, serverid: int
) -> Sequence[Project]:
    """
    Get projects by discord id
    :param conn: database connection
    :param discordid: discord id of user
    :return: list of project objects
    """
    query = (
        select(Project)
        .where(Project.owner_id == discordid, Project.server_id == serverid)
        .order_by(Project.created_at.desc())
    )
    result = await conn.execute(query)
    return result.scalars().all()


async def get_project(
    conn: AsyncSession, project_id: int, eager_load: bool = False
) -> Optional[Project]:
    """
    Get project by id
    :param conn: database connection
    :param project_id: project id
    :return: project object or None if not found
    """
    query = select(Project).where(Project.project_id == project_id)
    if eager_load:
        query = query.options(
            selectinload(Project.owner), selectinload(Project.members)
        )
    result = await conn.execute(query)
    return result.scalars().first()


async def update_project_team_size(conn, project_id: int) -> Optional[Project]:
    """
    Update the team size of a project by getting all roles associated with the project
    """
    query = select(Project).where(Project.project_id == project_id)
    result = await conn.execute(query)
    project: Project = result.scalars().first()
    if not project:
        return None
    # Get all roles associated with the project
    await conn.commit()
    await conn.refresh(project)
    return project


async def save_repository(conn, repo: Repository) -> Repository:
    """
    Save repo to database
    :param conn: database connection
    :param repo: repo object
    :return: None
    """
    repo = await conn.merge(repo)
    await conn.commit()
    return repo


async def add_member_to_project(
    conn: AsyncSession, project_id: int, github_id: int
) -> Optional[ProjectMember]:
    """
    Add a member to a project
    :param conn: database connection
    :param project_id: project id
    :param github_id: github id of the user to add
    :return: ProjectMember object if added, None if already exists
    """
    # Check if the member already exists in the project
    existing_member = await get_project_member(conn, project_id, github_id)
    if existing_member:
        return None  # Member already exists

    # Create a new ProjectMember object
    new_member = ProjectMember(
        project_id=project_id, user_id=github_id
    )  # Default role_id is set to 1
    conn.add(new_member)
    await conn.commit()
    await conn.refresh(new_member)
    return new_member


async def get_project_member(
    conn: AsyncSession, project_id: int, user_id: int
) -> Optional[ProjectMember]:
    """
    Get project member by project id and user id
    :param conn: database connection
    :param project_id: project id
    :param user_id: user id
    :return: project member object or None if not found
    """
    query = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id)
    result = await conn.execute(query)
    return result.scalars().first()


async def get_project_members(
    conn: AsyncSession, project_id: int
) -> Sequence[Tuple[ProjectMember, int]]:
    """
    Get all members of a project
    :param conn: database connection
    :param project_id: project id
    :return: list of project member objects
    """
    query = (
        select(ProjectMember, User.discord_id)
        .join(Github, ProjectMember.user_id == Github.github_id)
        .join(User, Github.discord_id == User.discord_id)
        .where(ProjectMember.project_id == project_id)
    )
    result = await conn.execute(query)
    rows = result.all()
    return [
        (row[0], row[1]) for row in rows
    ]  # Return a list of tuples (ProjectMember, discord_id)


async def remove_member_from_project(
    conn: AsyncSession, project_id: int, user_id: int
) -> bool:
    """
    Remove a member from a project
    :param conn: database connection
    :param project_id: project id
    :param user_id: user id
    :return: True if removed, False if not found
    """
    member = await get_project_member(conn, project_id, user_id)
    if not member:
        return False
    await conn.delete(member)
    await conn.commit()
    return True


async def assign_role_to_members(
    conn: AsyncSession,
    project_id: int,
    role_assignments: Dict[int, List[int]],  # role_id -> [github_id, ...]
) -> None:
    """
    Assign multiple members to roles for a given project.
    :param conn: async database session
    :param project_id: ID of the project
    :param role_assignments: mapping of role_id to list of github_ids
    """
    for role_id, github_ids in role_assignments.items():
        for github_id in github_ids:
            stmt = (
                update(ProjectMember)
                .where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == github_id,
                )
                .values(role_id=role_id)
            )
            await conn.execute(stmt)
    stmt = (
        update(Project)
        .where(Project.project_id == project_id)
        .values(member_assigned=True)
    )
    await conn.execute(stmt)
    await conn.commit()


async def get_participating_project(
    conn: AsyncSession, discord_id: int, serverid: int
) -> List[Project]:
    """
    Get all projects that a user is participating in.
    :param conn: database connection
    :param discord_id: discord id of the user
    :param serverid: server id of the user
    :return: list of Project objects
    """
    query = (select(Project) .join(ProjectMember,
                                   Project.project_id == ProjectMember.project_id,
                                   isouter=True) .where(or_(ProjectMember.user_id == discord_id,
                                                            Project.owner_id == discord_id),
                                                        Project.server_id == serverid,
                                                        ) .order_by(Project.created_at.desc()))
    result = await conn.execute(query)
    return result.scalars().all()
