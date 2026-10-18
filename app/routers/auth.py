import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import Role, User
from app.schemas import LoginRequest, LoginResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/mock-users", response_model=list[UserOut])
def list_mock_users(role: Role | None = None, db: Session = Depends(get_db)):
    """For the login page: shows users to pick from (MVP only)."""
    stmt = select(User).order_by(User.id)
    if role:
        stmt = stmt.where(User.role == role)
    return db.scalars(stmt).all()


@router.post("/mock-login", response_model=LoginResponse)
def mock_login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.get(User, body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.token = secrets.token_hex(32)
    db.commit()
    return LoginResponse(access_token=user.token, user_id=user.id,
                         name=user.name, role=user.role)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user