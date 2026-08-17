from __future__ import annotations

from app.database.session import Base, SessionLocal, engine
from app.demo_data.commerce_api import DEMO_REPO


def init_db() -> None:
    import app.models  # noqa: F401 ensures all models are registered on Base.metadata
    Base.metadata.create_all(bind=engine)
    _seed_demo_repository()


def _seed_demo_repository() -> None:
    from app.models.repository import Repository

    db = SessionLocal()
    try:
        existing = db.query(Repository).filter(Repository.full_name == DEMO_REPO["full_name"]).first()
        if existing:
            return
        repo = Repository(
            name=DEMO_REPO["name"], full_name=DEMO_REPO["full_name"], url=DEMO_REPO["url"],
            description=DEMO_REPO["description"], is_demo=True, status="UNSCANNED",
            primary_language=DEMO_REPO["primary_language"], languages=DEMO_REPO["languages"],
            frameworks=DEMO_REPO["frameworks"], package_managers=DEMO_REPO["package_managers"],
            dependency_files=DEMO_REPO["dependency_files"], file_count=DEMO_REPO["file_count"],
        )
        db.add(repo)
        db.commit()
    finally:
        db.close()
