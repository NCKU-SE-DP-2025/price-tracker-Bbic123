from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.auth.models import User
from src.auth.schemas import UserAuthSchema
from src.auth.service import (
    login_service,
    jwt_token_service,
    password_service,
    token_auth_service,
)
from src.database import database


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    database_session: Session = Depends(database.get_session),
):
    """login"""
    user = login_service.check_user_password_is_correct(
        database_session,
        form_data.username,
        form_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )
    access_token = jwt_token_service.create_access_token(
        base_claims={"sub": str(user.username)},
        expires_delta=timedelta(minutes=30),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def create_user(
    user: UserAuthSchema,
    database_session: Session = Depends(database.get_session),
):
    """create user"""
    hashed_password = password_service.hash_password(user.password)
    database_user = User(
        username=user.username,
        hashed_password=hashed_password,
    )
    database_session.add(database_user)
    database_session.commit()
    database_session.refresh(database_user)
    return database_user


@router.get("/me")
def get_users_me(
    current_user=Depends(
        token_auth_service.authenticate_user_token
    ),
):
    return {"username": current_user.username}
