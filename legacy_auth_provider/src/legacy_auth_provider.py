import json
import os
from contextlib import asynccontextmanager
from arxiv.config import settings
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Tuple
import logging


from arxiv.db import configure_db, Session as DatabaseSession
from arxiv.db.models import TapirUser, TapirUsersPassword, TapirNickname, Demographic, State

from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.bizmodels.tapir_to_kc_mapping import (get_tapir_user, AuthResponse,
                                                          user_model_to_auth_response, PasswordData,
                                                          authenticate_password)


UserProfile = Tuple[TapirUser, TapirUsersPassword, TapirNickname, Demographic]

logger = logging.getLogger(__name__)

app = FastAPI()

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if token != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return token

@app.get("/")
async def root():
    return {"message": "Hello"}


@app.get("/auth/{name}", response_model=AuthResponse)
async def get_auth_name(name: str, _token: str=Depends(verify_token)) -> AuthResponse:
    with DatabaseSession() as session:
        tapir_user = get_tapir_user(session, name)

        if not tapir_user:
            raise HTTPException(status_code=404, detail="User not found")

        um = UserModel.one_user(session, tapir_user.user_id)
        return user_model_to_auth_response(um, tapir_user)


@app.post("/auth/{name}")
async def validate_user(name: str, pwd: PasswordData, _token: str=Depends(verify_token)):
    with DatabaseSession() as session:
        tapir_user = get_tapir_user(session, name)
        if not tapir_user:
            raise HTTPException(status_code=404, detail="User not found")

        if tapir_user.flag_banned:
            raise HTTPException(status_code=403, detail="User is banned")

        if tapir_user.flag_deleted:
            raise HTTPException(status_code=410, detail="User is deleted")

        if authenticate_password(session, tapir_user, pwd.password):
            # Placeholder for actual password validation logic
            return {"message": "User validated successfully"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    pass


@app.get("/states", response_model=dict)
async def health_check() -> dict:

    result = {"/cloudsql": os.listdir("/cloudsql")}
    result.update({"env": repr(os.environ)})

    csql_readme = "/cloudsql/README"
    if os.path.exists(csql_readme):
        try:
            with open(csql_readme, "r") as f:
                result.update({"csql_readme": f.read()})
                pass
        except Exception as exc:
            logger.info(csql_readme + ": " + str(exc), exc_info=True)
            pass
        pass

    try:
        with DatabaseSession() as session:
            states: State = session.query(State).all()
            result = result.update({state.name: state.value for state in states})
            logger.info(json.dumps(result, indent=2))
            return result

    except Exception as e:
        logger.info(json.dumps(result, indent=2))
        raise HTTPException(status_code=500, detail=str(e) + repr(os.environ))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.debug('start')
    engine, _ = configure_db(settings)
    logger.debug(f"Engine: {engine.name}, DBURI: {settings.CLASSIC_DB_URI}")
    try:
        with DatabaseSession() as session:
            tapir_user = get_tapir_user(session, "ph18@cornell.edu")
            if tapir_user:
                um = UserModel.one_user(session, tapir_user.user_id)
                logger.info(f"TapirUser: {str(user_model_to_auth_response(um, tapir_user))}")
    except Exception as _exc:
        logger.error("Database connection error")

    yield  # this yields control to the app
