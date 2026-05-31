from sqlalchemy.orm import Session

from app.dal.db_models import Users


def get_user_by_email(db: Session, email: str) -> Users | None:
    return db.query(Users).filter(Users.email == email).first()


def get_user_pages(user: Users) -> list[dict]:
    seen = set()
    pages = []
    for role in user.role:
        for page in role.page:
            if page.slug not in seen:
                seen.add(page.slug)
                pages.append({"slug": page.slug, "label": page.label, "icon": page.icon})
    return pages


def create_user(db: Session, email: str, name: str | None, password_hash: str) -> Users:
    user = Users(email=email, name=name, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
