import json
from datetime import date, datetime, time

from sqlalchemy import (JSON, TIMESTAMP, VARCHAR, BigInteger, Boolean, Column,
                        DateTime, Float, ForeignKey, Integer, String, Table,
                        Text, UniqueConstraint, func, inspect)
from sqlalchemy.orm import relationship

try:
    from .basemodel import Base
except ImportError:
    from basemodel import Base


class User(Base):
    __tablename__ = "user"
    discord_id = Column(BigInteger, primary_key=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires = Column(DateTime, nullable=True)
    last_check = Column(TIMESTAMP, nullable=True, default=datetime.now)
    coding_style = Column(Text, nullable=True)  # LLM 분석 결과 저장
    github_account = relationship(
        "Github", back_populates="user", cascade="all, delete-orphan"
    )
    notion_account = relationship(
        "Notion", back_populates="user", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )


class Github(Base):
    __tablename__ = "github"
    # GitHub user ID (or developer ID)
    github_id = Column(BigInteger, primary_key=True)
    discord_id = Column(
        BigInteger,
        ForeignKey("user.discord_id"),
        nullable=False)
    github_login = Column(Text, nullable=True)  # 깃허브 로그인명 (기존 Github 모델)

    primary_languages = Column(JSON, nullable=True)
    experience_years = Column(Float, nullable=True)
    total_stars = Column(Integer, nullable=True)
    public_repos = Column(Integer, nullable=True)
    total_forks = Column(Integer, nullable=True)
    profile_created_at = Column(DateTime, nullable=True)
    last_active_date = Column(DateTime, nullable=True)

    repositories = relationship(
        "Repository",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    user = relationship(
        "User",
        back_populates="github_account",
        passive_deletes=True)
    memberof = relationship(
        "ProjectMember", back_populates="github_account", passive_deletes=True
    )


class Notion(Base):
    __tablename__ = "notion"
    notion_id = Column(BigInteger, primary_key=True)
    discord_id = Column(
        BigInteger,
        ForeignKey(
            "user.discord_id",
            ondelete="CASCADE"))
    notion_login = Column(Text, nullable=False)

    user = relationship("User", back_populates="notion_account")


class ServerInfo(Base):
    __tablename__ = "server_info"
    server_id = Column(BigInteger, primary_key=True)
    mod_id = Column(BigInteger, nullable=True)
    notion_token = Column(Text, nullable=True)
    notification_channel_id = Column(BigInteger, nullable=True)
    webhook_channel_id = Column(BigInteger, nullable=True)
    updated = Column(DateTime, nullable=True, default=datetime.now)

    notion_databases = relationship(
        "NotionDatabase", back_populates="server", cascade="all, delete-orphan"
    )
    notion_tags = relationship(
        "NotionTags", back_populates="server", cascade="all, delete-orphan"
    )

    def todict(self, exclude=None, datetime_format="%Y-%m-%d %H:%M:%S"):
        result = super().todict(exclude, datetime_format)
        state = inspect(self)
        if "notion_databases" in state.unloaded:
            pass
        else:
            result["notion_databases"] = [
                {
                    "database_id": db.database_id,
                    "database_name": db.database_name,
                    "channel_id": db.channel_id,
                }
                for db in self.notion_databases
            ]
        if "notion_tags" in state.unloaded:
            pass
        else:
            result["notion_tags"] = [
                {"idx": tag.idx, "tag": tag.tag} for tag in self.notion_tags
            ]
        return result


class ShowGithub(Base):
    __tablename__ = "show_github"
    server_id = Column(
        BigInteger,
        ForeignKey("server_info.server_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = Column(
        BigInteger,
        ForeignKey(
            "user.discord_id",
            ondelete="CASCADE"),
        primary_key=True)
    show = Column(Boolean, nullable=False, default=False)


class NotionDatabase(Base):
    __tablename__ = "notion_database"
    server_id = Column(
        BigInteger, ForeignKey("server_info.server_id", ondelete="CASCADE")
    )
    channel_id = Column(BigInteger, nullable=False)
    database_id = Column(VARCHAR(40), primary_key=True)
    database_name = Column(Text, nullable=True)

    server = relationship("ServerInfo", back_populates="notion_databases")
    pages = relationship(
        "NotionPages", back_populates="database", cascade="all, delete-orphan"
    )


class NotionPages(Base):
    __tablename__ = "notion_pages"
    page_id = Column(VARCHAR(40), primary_key=True)
    database_id = Column(
        VARCHAR(40),
        ForeignKey(
            "notion_database.database_id",
            ondelete="CASCADE"))
    thread_id = Column(BigInteger, nullable=True)
    updated = Column(Boolean, nullable=False, default=False)
    blocked = Column(Boolean, nullable=False, default=False)

    database = relationship("NotionDatabase", back_populates="pages")


class NotionTags(Base):
    __tablename__ = "notion_tags"
    idx = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(
        BigInteger, ForeignKey("server_info.server_id", ondelete="CASCADE")
    )
    tag = Column(VARCHAR(100), nullable=False)
    __table_args__ = (
        UniqueConstraint(
            "server_id",
            "tag",
            name="uq_server_tag"),
    )
    server = relationship("ServerInfo", back_populates="notion_tags")


class Repository(Base):
    __tablename__ = "repositories"

    repo_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey(
            "github.github_id",
            ondelete="CASCADE"),
        nullable=False)

    name = Column(String(30), nullable=False)
    url = Column(String(100), unique=True, nullable=False)
    primary_language = Column(String(20), nullable=True)
    stars = Column(Integer, nullable=False)
    forks = Column(Integer, nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=True)  # 프로젝트 분야 태그
    core_features = Column(JSON, nullable=True)  # 레포지토리 주요 기능들

    owner = relationship("Github", back_populates="repositories")


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(
        BigInteger,
        ForeignKey(
            "user.discord_id",
            ondelete="CASCADE"),
        nullable=False)
    server_id = Column(
        BigInteger,
        ForeignKey("server_info.server_id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    team_size = Column(Integer, nullable=True)
    core_features = Column(JSON, nullable=False)
    tech_stack = Column(JSON, nullable=False)
    complexity = Column(String(20), nullable=False)
    database = Column(String(100), nullable=True)
    platform = Column(String(20), nullable=False)
    notifications = Column(Boolean, default=False)
    map_integration = Column(Boolean, default=False)
    auth_required = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="projects")
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(
        Integer,
        ForeignKey(
            "projects.project_id",
            ondelete="CASCADE"),
        primary_key=True)
    user_id = Column(
        BigInteger,
        ForeignKey(
            "github.github_id",
            ondelete="CASCADE"),
        primary_key=True)

    project = relationship("Project", back_populates="members")
    github_account = relationship("Github", back_populates="memberof")


class DMchannel(Base):
    __tablename__ = "dm_channels"
    user_id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, nullable=True)
    blocked = Column(Boolean, nullable=False, default=False)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
