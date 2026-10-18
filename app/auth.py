from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Role, User

bearer = HTTPBearer()


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer),
                     db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.token == cred.credentials))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def require_role(*roles: Role):
    """Usage: user = Depends(require_role(Role.admin))"""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission for this action")
        return user
    return checker