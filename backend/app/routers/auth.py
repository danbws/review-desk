from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.gateway.deps import current_user, get_db
from app.models import User
from app.schemas import Credentials, TokenOut, UserOut
from app.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token(request: Request, user: User) -> TokenOut:
    s = request.app.state.settings
    return TokenOut(access_token=create_token(user.id, s.jwt_secret, s.jwt_expire_minutes))


@router.post("/signup", response_model=TokenOut, status_code=201)
def signup(body: Credentials, request: Request, db: Session = Depends(get_db)):
    request.app.state.auth_limiter.check(f"ip:{request.client.host if request.client else '?'}")
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from None
    return _token(request, user)


@router.post("/login", response_model=TokenOut)
def login(body: Credentials, request: Request, db: Session = Depends(get_db)):
    request.app.state.auth_limiter.check(f"ip:{request.client.host if request.client else '?'}")
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _token(request, user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
