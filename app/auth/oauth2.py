from fastapi.security import OAuth2AuthorizationCodeBearer
from app.config import settings

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
    auto_error=False
)
