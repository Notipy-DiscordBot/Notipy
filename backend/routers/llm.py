import json
import re
from datetime import datetime, timezone

from common import *
from fastapi import (APIRouter, BackgroundTasks, Body, Depends, HTTPException,
                     Request, Response, status)
from github import Github
from pydantic import BaseModel
from services import llmservice, userservice
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

router = APIRouter(prefix="/llm")


def build_project_prompt(name: str, description: str) -> str:
    return f"""
You are a data engineer. Given the following project description, fill in all required fields
for the `projects` table.

Respond ONLY with valid JSON. The response MUST include ALL of the following keys exactly as shown:
- category
- core_features (a list)
- tech_stack (a list)
- complexity (low/medium/high)
- database (string)
- platform (web/mobile/both)
- notifications (true/false)
- map_integration (true/false)
- auth_required (true/false)

The response must be a valid JSON object with no explanations or comments.
For example:
{{
  "category": "travel",
  "core_features": ["Personalized suggestions", "Map integration", "User reviews"],
  "tech_stack": ["React", "Node.js", "PostgreSQL"],
  "complexity": "medium",
  "database": "PostgreSQL",
  "platform": "web",
  "notifications": true,
  "map_integration": true,
  "auth_required": true
}}

Project name: {name}
Project Description: {description}
"""


@router.get("/projects/{owner_id}/server/{serverid}")
@checkInternalServer
async def get_project(
    request: Request, owner_id: int, serverid: int, conn=Depends(get_db)
):
    """
    주어진 owner_id에 해당하는 프로젝트 정보를 JSON 형식으로 반환합니다.
    """
    res = await llmservice.get_projects_by_owner(conn, owner_id, serverid)
    if not res:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    projects = [proj.todict() for proj in res]
    return JSONResponse(status_code=200, content={"projects": projects})


@router.put("/projects/{owner_id}/{project_id}")
async def update_project(
        owner_id: int,
        project_id: int,
        updates: dict = Body(...),
        conn=Depends(get_db)):
    try:
        updated_project = await llmservice.set_projects(conn, project_id, updates)
        return {
            "message": "Project updated successfully",
            "project": updated_project.todict(),
        }
    except ValueError as e:
        return Response(status_code=204)


@router.delete("/projects/{owner_id}/{project_id}")
@checkInternalServer
async def delete_project(
    request: Request, owner_id: int, project_id: int, conn=Depends(get_db)
):
    """
    주어진 owner_id와 project_id에 해당하는 프로젝트를 삭제합니다.
    """
    res = await llmservice.delete_project(conn, owner_id, project_id)
    if not res:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Project deleted successfully"},
    )


class ProjectItems(BaseModel):
    name: str
    serverid: int
    description: str


@router.post("/projects/{owner_id}")
@checkInternalServer
async def analyze_project(
    request: Request,
    owner_id: int,
    items: ProjectItems,
    conn=Depends(get_db),
    llm: OllamaChat = Depends(get_llm),
):
    """
    LLM에 프로젝트 설명을 보내고, JSON 형식으로 응답을 받아서 파싱합니다.
    """
    prompt = build_project_prompt(items.name, items.description)
    response = llm.ask(
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        format="json",
    )
    response = json.loads(response)
    proj = llmservice.Project(
        name=items.name,
        owner_id=owner_id,
        server_id=items.serverid,
        description=items.description,
        category=response.get("category"),
        team_size=4,
        core_features=response["core_features"],
        tech_stack=response["tech_stack"],
        complexity=response["complexity"],
        database=response.get("database"),
        platform=response["platform"],
        notifications=response.get("notifications", False),
        map_integration=response.get("map_integration", False),
        auth_required=response.get("auth_required", False),
    )
    res = await llmservice.create_project(conn, proj)
    if not res:
        raise HTTPException(status_code=500, detail="Failed to save project")
    return JSONResponse(
        status_code=200, content={"status": "success", "data": res.todict()}
    )


@router.post("/git/{discorduserid}")
@checkInternalServer
async def analyze_github_user(
        request: Request,
        discorduserid: int,
        bgtask: BackgroundTasks,
        conn=Depends(get_db)):
    """
    GitHub 사용자 정보를 분석하여 JSON 형식으로 응답합니다.
    """
    res = await userservice.get_user(conn, discorduserid)
    if not res:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    discord, git, notion = res

    gh = Github(GITHUB_TOKEN)

    user = gh.get_user_by_id(git.github_id)
    repos = list(user.get_repos())
    # 언어 통계
    langs = {}
    for r in repos:
        for lang, cnt in r.get_languages().items():
            langs[lang] = langs.get(lang, 0) + cnt
    primary_langs = sorted(langs, key=langs.get, reverse=True)[:3]

    # 별·포크 합계
    total_stars = sum(r.stargazers_count for r in repos)
    total_forks = sum(r.forks_count for r in repos)

    # 마지막 활동 날짜 (각 repo의 최신 커밋 일자 중 최대)
    last_dates = []
    for r in repos:
        try:
            commit = r.get_commits()[0]
            last_dates.append(commit.commit.author.date)
        except Exception:
            pass
    last_active = max(last_dates) if last_dates else None
    git.primary_languages = primary_langs
    git.experience_years = (
        round((datetime.now(timezone.utc) - user.created_at).days / 365, 1),
    )
    git.public_repos = user.public_repos
    git.total_stars = total_stars
    git.total_forks = total_forks
    git.profile_created_at = user.created_at
    git.last_active_date = last_active
    res = await userservice.update_github(conn, git)
    if not res:
        raise HTTPException(
            status_code=500,
            detail="Failed to update GitHub user")
    top5 = sorted(repos, key=lambda r: r.stargazers_count, reverse=True)[:5]
    bgtask.add_task(analyze_github_repo, conn, top5, res)
    return JSONResponse(
        status_code=200,
        content={
            "data": git.todict(),
            "repos": None})


def fill_repo_metadata(name: str, url: str, readme: str, llm) -> dict:
    prompt = (
        "You are a data engineer. Given the following GitHub repository metadata, "
        "please infer and return a JSON object with two keys:\n"
        "  - category: project domain (e.g., game, web, data, devops)\n"
        "  - core_features: list of 3–5 main features of this repository\n"
        "Respond with valid JSON only.\n\n"
        f"Repository Name: {name}\n"
        f"Repository URL: {url}\n"
        f"README Content:\n```\n{readme}\n```\n"
    )
    resp = llm.ask(
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        format="json",
    )
    return json.loads(resp)


async def analyze_github_repo(conn, top5, user_rec):
    llm = get_llm()
    for r in top5:
        readme_content = None
        try:
            readme_file = r.get_readme()
            readme_content = readme_file.decoded_content.decode("utf-8")
        except Exception:
            readme_content = "내용이 없거나 불러오기 실패"

        repo_rec = llmservice.Repository(
            user_id=user_rec.github_id,
            name=r.name,
            url=r.html_url,
            primary_language=r.language,
            stars=r.stargazers_count,
            forks=r.forks_count,
            description=readme_content,
            category=None,
            core_features=[],
        )

        # LLM 호출: category & core_features 채우기
        try:
            meta = fill_repo_metadata(r.name, r.html_url, readme_content, llm)
            repo_rec.category = meta.get("category")
            repo_rec.core_features = meta.get("core_features", [])
        except Exception as e:
            print(f"LLM 메타데이터 호출 실패 for {r.name}: {e}")

        # DB에 저장
        res = await llmservice.save_repository(conn, repo_rec)


@router.get("/project/{owner_id}/{projectid}/member")
@checkInternalServer
async def get_project_members(
    request: Request, owner_id: int, projectid: int, conn=Depends(get_db)
):
    """
    주어진 프로젝트 ID에 해당하는 프로젝트의 멤버 목록을 JSON 형식으로 반환합니다.
    """
    result = await llmservice.get_project_members(conn, project_id=projectid)
    if not result:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    returndict = []
    for res in result:
        member, discord_id = res
        returndict.append(
            {"githubid": member.user_id, "discordid": discord_id})
    return JSONResponse(status_code=200, content={"members": returndict})


@router.get("/project/participating/{user_id}/{serverid}")
@checkInternalServer
async def get_participated_projects(
    request: Request, user_id: int, serverid: int, conn=Depends(get_db)
):
    """
    주어진 사용자 ID에 해당하는 사용자가 참여한 프로젝트 목록을 JSON 형식으로 반환합니다.
    """
    projects = await llmservice.get_participating_project(conn, user_id, serverid)
    if not projects:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    project_list = [project.todict() for project in projects]
    return JSONResponse(status_code=200, content={"projects": project_list})


@router.post("/project/{owner_id}/{projectid}/member")
@checkInternalServer
async def add_member_to_project(
    request: Request,
    owner_id: int,
    projectid: int,
    user_id: int = Body(...),
    conn=Depends(get_db),
    llm=Depends(get_llm),
):
    """
    주어진 사용자 ID를 프로젝트에 추가합니다.
    """
    user = await userservice.get_user(conn, discordid=user_id)
    if not user:
        return JSONResponse(
            status_code=400,
            content={"message": "User does not have a linked GitHub account"},
        )
    discord, github, notion = user
    if not github:
        return JSONResponse(
            status_code=400,
            content={"message": "User does not have a linked GitHub account"},
        )

    project = await llmservice.get_project(conn, project_id=projectid, eager_load=True)
    if not project:
        return Response(status_code=204)

    if project.owner_id == user_id:
        return JSONResponse(
            status_code=409,
            content={"message": "Project owner cannot be added as a member"},
        )

    # 프로젝트 멤버가 이미 존재하는지 확인
    existing_member = next(
        (m for m in project.members if m.user_id == github.github_id), None
    )
    if existing_member:
        return JSONResponse(
            status_code=409,
            content={"message": "User is already a member of the project"},
        )

    # 멤버 추가 로직
    member = await llmservice.add_member_to_project(conn, projectid, github.github_id)
    return JSONResponse(
        status_code=200, content={
            "message": "User added to project successfully"})


@router.delete("/project/{owner_id}/{projectid}/member/{user_id}")
@checkInternalServer
async def remove_member_from_project(
    request: Request,
    owner_id: int,
    projectid: int,
    user_id: int,
    conn=Depends(get_db),
    llm=Depends(get_llm),
):
    """
    주어진 사용자 ID를 프로젝트에서 제거합니다.
    """
    project = await llmservice.get_project(conn, project_id=projectid, eager_load=True)
    if not project:
        return Response(status_code=204)

    # 프로젝트 멤버가 존재하는지 확인
    existing_member = next(
        (m for m in project.members if m.user_id == user_id), None)
    if not existing_member:
        return JSONResponse(
            status_code=404, content={
                "message": "User is not a member of the project"})

    # 멤버 제거 로직 (예: DB에서 삭제)
    await llmservice.remove_member_from_project(conn, projectid, user_id)

    return JSONResponse(
        status_code=200, content={
            "message": "User removed from project successfully"})


@router.post("/project/{owner_id}/{projectid}/assign/auto")
@checkInternalServer
async def assign_users_to_roles(
    request: Request,
    owner_id: int,
    projectid: int,
    conn: AsyncSession = Depends(get_db),
    agent=Depends(get_agent),
):
    # 1. 프로젝트 조회 (eager load)
    project = await llmservice.get_project(conn, projectid, eager_load=True)
    if not project or project.owner_id != owner_id:
        return {}, status.HTTP_204_NO_CONTENT

    roles = await llmservice.get_roles(conn, projectid)
    if not roles:
        return Response(status_code=204)

    members = await get_project_members(conn, projectid)
    if not members:
        return Response(status_code=204)

    if not project.team_size:
        return Response(status_code=204)
    # 2. LLM 평가 준비
    role_results = [[] for _ in range(len(roles))]

    # 3. 각 팀원에 대해 역할 평가
    for member, _ in members:
        user = member.github_account
        user_repos = user.repositories[:5]
        user_data = {
            "name": user.github_login,
            "primary_languages": user.primary_languages,
            "experience_years": user.experience_years,
            "public_repos": user.public_repos,
            "total_stars": user.total_stars,
            "total_forks": user.total_forks,
            "profile_created_at": (
                user.profile_created_at.isoformat() if user.profile_created_at else None
            ),
            "last_active_date": (
                user.last_active_date.isoformat() if user.last_active_date else None
            ),
            "repositories": [
                {
                    "name": repo.name,
                    "url": repo.url,
                    "primary_language": repo.primary_language,
                    "stars": repo.stars,
                    "forks": repo.forks,
                }
                for repo in user_repos
            ],
        }

        for idx, role in enumerate(roles):
            prompt_data = {
                "role": {
                    "role_id": role.role_id,
                    "name": role.name,
                    "description": role.description,
                    "languages_tools": role.languages_tools,
                },
                "user": user_data,
                "project": {
                    "name": project.name,
                    "description": project.description,
                    "tech_stack": project.tech_stack,
                },
            }
            prompt_message = (
                "Using the provided user, role, and project information in JSON format, "
                "evaluate the user's suitability for the role. "
                'Return ONLY a JSON object like this: {"score": <integer>}. '
                "Data: " +
                json.dumps(
                    prompt_data,
                    ensure_ascii=False))

            response = await agent.ask_async(prompt_message)
            match = re.search(r"```json(.*?)```", response, re.DOTALL)
            json_str = (
                match.group(1).strip()
                if match
                else response[response.find("{"): response.rfind("}") + 1]
            )
            try:
                result = json.loads(json_str)
                score = result.get("score", 0)
            except Exception:
                score = 0

            role_results[idx].append((user.github_id, score))

    # 4. 점수 기반 역할 배정 (exclusive)
    candidate_pool = []
    for role_idx, candidates in enumerate(role_results):
        for github_id, score in candidates:
            candidate_pool.append((role_idx, github_id, score))
    candidate_pool.sort(key=lambda x: x[2], reverse=True)

    assigned_users = set()
    assignments = {i: [] for i in range(len(roles))}

    for role_idx, github_id, score in candidate_pool:
        if github_id in assigned_users:
            continue
        if len(assignments[role_idx]) < roles[role_idx].count:
            assignments[role_idx].append(github_id)
            assigned_users.add(github_id)

    # 5. DB 업데이트: ProjectMember.role_id 설정

    # 역할 할당 딕셔너리 생성: role_id 기준
    role_assignments = {
        project.roles[role_idx].role_id: github_ids
        for role_idx, github_ids in assignments.items()
    }

    # DB에 반영
    await llmservice.assign_role_to_members(conn, project.project_id, role_assignments)
    # github_id → discord_id 매핑
    github_to_discord = {
        github_id: discord_id
        for member, discord_id in members
        for github_id_in_member in [member.github_account.github_id]
        if github_id == github_id_in_member
    }

    # 최종 결과 생성
    result = {}
    for i, github_ids in assignments.items():
        role_name = roles[i].name
        discord_ids = [
            github_to_discord.get(gid)
            for gid in github_ids
            if github_to_discord.get(gid)
        ]
        result[role_name] = discord_ids

    return JSONResponse(status_code=200, content={"data": result})
