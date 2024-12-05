from fastapi.responses import JSONResponse
from fastapi import Request, Depends, HTTPException 
from sqlalchemy.orm import Session
from connect import get_db
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from models import User
from google.cloud import secretmanager
import os
import logging

secret_client = secretmanager.SecretManagerServiceClient()

def access_secret_version(secret_id: str, version_id: str = "latest") -> str:

    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        secret_name = f"projects/{'skinsift-2024'}/secrets/{secret_id}/versions/{version_id}"
        response = secret_client.access_secret_version(name=secret_name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.error(f"Error accessing secret {secret_id}: {e}")
        raise

# Load secrets dari Secret Manager
try:
    SECRET_KEY = access_secret_version("secret_key")
    ACCESS_TOKEN_EXPIRE_DAYS = int(access_secret_version("ACCESS_TOKEN_EXPIRE_DAYS"))
    ALGORITHM = access_secret_version("ALGORITHM")
except Exception as e:
    raise ValueError("Error loading secrets: " + str(e))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        print(f"Decoded user_id: {user_id}")  # Debugging output
        if user_id is None:
            raise credentials_exception
        user = db.query(User).filter(User.Users_ID == user_id).first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user