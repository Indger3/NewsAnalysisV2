import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dal.app_db import get_db
from app.dal import admin_dal
from app.utils.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Pydantic schemas ───────────────────────────────────────────────────────

class PageOut(BaseModel):
    id: uuid.UUID
    slug: str
    label: str
    icon: Optional[str] = None

    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    pages: list[PageOut] = []

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    is_active: bool
    roles: list[RoleOut] = []

    model_config = {"from_attributes": True}


class SetActiveBody(BaseModel):
    is_active: bool


class SetRolesBody(BaseModel):
    role_ids: list[uuid.UUID]


class CreateRoleBody(BaseModel):
    name: str
    description: Optional[str] = None


class SetPagesBody(BaseModel):
    page_ids: list[uuid.UUID]


class CreatePageBody(BaseModel):
    slug: str
    label: str
    icon: Optional[str] = None


# ── Users ──────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    users = admin_dal.get_all_users(db)
    return [
        UserOut(
            id=u.id,
            email=u.email,
            name=u.name,
            is_active=u.is_active,
            roles=[RoleOut(id=r.id, name=r.name, description=r.description,
                           pages=[PageOut(id=p.id, slug=p.slug, label=p.label, icon=p.icon) for p in r.page])
                   for r in u.role],
        )
        for u in users
    ]


@router.put("/users/{user_id}")
def update_user(
    user_id: uuid.UUID,
    body: SetActiveBody,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    user = admin_dal.set_user_active(db, user_id, body.is_active)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user.id), "is_active": user.is_active}


@router.put("/users/{user_id}/roles")
def update_user_roles(
    user_id: uuid.UUID,
    body: SetRolesBody,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    user = admin_dal.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = admin_dal.set_user_roles(db, user, body.role_ids)
    return {
        "id": str(user.id),
        "roles": [{"id": str(r.id), "name": r.name} for r in user.role],
    }


# ── Roles ──────────────────────────────────────────────────────────────────

@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    roles = admin_dal.get_all_roles(db)
    return [
        RoleOut(
            id=r.id,
            name=r.name,
            description=r.description,
            pages=[PageOut(id=p.id, slug=p.slug, label=p.label, icon=p.icon) for p in r.page],
        )
        for r in roles
    ]


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    body: CreateRoleBody,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    role = admin_dal.create_role(db, body.name, body.description)
    return RoleOut(id=role.id, name=role.name, description=role.description)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    if not admin_dal.delete_role(db, role_id):
        raise HTTPException(status_code=404, detail="Role not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/roles/{role_id}/pages")
def update_role_pages(
    role_id: uuid.UUID,
    body: SetPagesBody,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    role = admin_dal.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role = admin_dal.set_role_pages(db, role, body.page_ids)
    return {
        "id": str(role.id),
        "pages": [{"id": str(p.id), "slug": p.slug} for p in role.page],
    }


# ── Pages ──────────────────────────────────────────────────────────────────

@router.get("/pages", response_model=list[PageOut])
def list_pages(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return admin_dal.get_all_pages(db)


@router.post("/pages", response_model=PageOut, status_code=status.HTTP_201_CREATED)
def create_page(
    body: CreatePageBody,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    page = admin_dal.create_page(db, body.slug, body.label, body.icon)
    return PageOut(id=page.id, slug=page.slug, label=page.label, icon=page.icon)


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(
    page_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    if not admin_dal.delete_page(db, page_id):
        raise HTTPException(status_code=404, detail="Page not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
