import uuid
from typing import Optional
from emails import send_email
from fastapi.background import BackgroundTasks

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from app.db import User, get_user_db

SECRET = "SECRET"

background_tasks = BackgroundTasks()

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET
    
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        return("User Successfully Registered")
        

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        background_tasks.add_task(send_password_email, user.email,token)
        print(f"User {user.id} has forgot their password. Reset token: {token}")
####### please use two fields in the password reset form
####### new_Password and confirm_password and if they match send the new_Pass
####### to /auth/reset-password route
    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):

        background_tasks.add_task(send_email, user.email, token)
        print(f"Verification requested for user {user.id}. Verification token: {token}")
    
    async def on_after_verify(
        self, user: User, request: Optional[Request] = None
    ):
        print(f"User {user.id} has been verified")



async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


################## Custom Class ########################

#########################


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True,superuser=True)





