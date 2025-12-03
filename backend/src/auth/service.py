from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.auth.models import User
from src.database import database


oauth2_bearer_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


class PasswordService:
    def __init__(self):
        self.password_context = CryptContext(
            schemes=["bcrypt"], deprecated="auto"
        )

    def hash_password(self, plain_password: str) -> str:
        return self.password_context.hash(plain_password)

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        return self.password_context.verify(plain_password, hashed_password)


class JwtTokenService:
    def __init__(
        self,
        secret_key: str = "1892dhianiandowqd0n",
        algorithm: str = "HS256",
        token_expire_minutes: int = 15,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes

    def create_access_token(
        self,
        base_claims: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        to_encode = base_claims.copy()
        if expires_delta:
            expires_at_utc = datetime.utcnow() + expires_delta
        else:
            expires_at_utc = datetime.utcnow() + timedelta(
                minutes=self.token_expire_minutes
            )
        to_encode.update({"exp": expires_at_utc})
        print(to_encode)
        encoded_jwt = jwt.encode(to_encode, self.secret_key, self.algorithm)
        return encoded_jwt

    def decode_access_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])


class LoginService:
    def __init__(self, password_service: PasswordService):
        self.password_service = password_service

    def check_user_password_is_correct(
        self,
        database_session: Session,
        username: str,
        plain_password: str,
    ):
        user = (
            database_session.query(User)
            .filter(User.username == username)
            .first()
        )
        if not user:
            return False
        if not self.password_service.verify_password(
            plain_password,
            user.hashed_password,
        ):
            return False
        return user


class TokenAuthService:
    def __init__(self, jwt_token_service: JwtTokenService):
        self.jwt_token_service = jwt_token_service

    def authenticate_user_token(
        self,
        access_token=Depends(oauth2_bearer_scheme),
        database_session: Session = Depends(database.get_session),
    ):
        token_payload = self.jwt_token_service.decode_access_token(
            access_token
        )
        return (
            database_session.query(User)
            .filter(User.username == token_payload.get("sub"))
            .first()
        )


password_service = PasswordService()
jwt_token_service = JwtTokenService()
login_service = LoginService(password_service)
token_auth_service = TokenAuthService(jwt_token_service)
