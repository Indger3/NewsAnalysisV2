import uuid
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.dal.db_models import Pages, Roles, Users


# ── Users ──────────────────────────────────────────────────────────────────

def get_all_users(db: Session) -> list[Users]:
    return (
        db.query(Users)
        .options(selectinload(Users.role).selectinload(Roles.page))
        .order_by(Users.created_at)
        .all()
    )


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[Users]:
    return (
        db.query(Users)
        .options(selectinload(Users.role))
        .filter(Users.id == user_id)
        .first()
    )


def set_user_active(db: Session, user_id: uuid.UUID, is_active: bool) -> Optional[Users]:
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        return None
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def set_user_roles(db: Session, user: Users, role_ids: list[uuid.UUID]) -> Users:
    roles = db.query(Roles).filter(Roles.id.in_(role_ids)).all()
    user.role = roles
    db.commit()
    db.refresh(user)
    return user


# ── Roles ──────────────────────────────────────────────────────────────────

def get_all_roles(db: Session) -> list[Roles]:
    return (
        db.query(Roles)
        .options(selectinload(Roles.page))
        .order_by(Roles.created_at)
        .all()
    )


def get_role_by_id(db: Session, role_id: uuid.UUID) -> Optional[Roles]:
    return (
        db.query(Roles)
        .options(selectinload(Roles.page))
        .filter(Roles.id == role_id)
        .first()
    )


def create_role(db: Session, name: str, description: Optional[str]) -> Roles:
    role = Roles(name=name, description=description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: uuid.UUID) -> bool:
    role = db.query(Roles).filter(Roles.id == role_id).first()
    if not role:
        return False
    db.delete(role)
    db.commit()
    return True


def set_role_pages(db: Session, role: Roles, page_ids: list[uuid.UUID]) -> Roles:
    pages = db.query(Pages).filter(Pages.id.in_(page_ids)).all()
    role.page = pages
    db.commit()
    db.refresh(role)
    return role


# ── Pages ──────────────────────────────────────────────────────────────────

def get_all_pages(db: Session) -> list[Pages]:
    return db.query(Pages).order_by(Pages.slug).all()


def get_page_by_id(db: Session, page_id: uuid.UUID) -> Optional[Pages]:
    return db.query(Pages).filter(Pages.id == page_id).first()


def create_page(db: Session, slug: str, label: str, icon: Optional[str]) -> Pages:
    page = Pages(slug=slug, label=label, icon=icon)
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def delete_page(db: Session, page_id: uuid.UUID) -> bool:
    page = db.query(Pages).filter(Pages.id == page_id).first()
    if not page:
        return False
    db.delete(page)
    db.commit()
    return True
