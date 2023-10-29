from fastapi.security import HTTPBearer

from quokka_editor_back.auth.authentication import Auth

auth_handler = Auth()
security = HTTPBearer()

__all__ = ("auth_handler", "security")
