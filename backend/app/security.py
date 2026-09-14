from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User
password_hash = PasswordHash.recommended()
bearer = HTTPBearer()
def hash_password(value): return password_hash.hash(value)
def verify_password(value, hashed): return password_hash.verify(value, hashed)
def create_token(user): return jwt.encode({"sub": user.id, "exp": datetime.now(timezone.utc)+timedelta(hours=8)}, settings.jwt_secret, algorithm="HS256")
def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    try: user_id = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])["sub"]
    except Exception: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, user_id)
    if not user or not user.is_active: raise HTTPException(status_code=401, detail="Inactive user")
    return user
def require(permission):
    def check(user: User = Depends(current_user)):
        granted = {p.permission for p in user.permissions}
        if permission not in granted: raise HTTPException(status_code=403, detail="Permission denied")
        return user
    return check
