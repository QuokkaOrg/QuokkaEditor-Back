from fastapi.security import HTTPBearer

from quokka_editor_back.auth.authentication import Auth

auth_handler = Auth()
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

__all__ = ("auth_handler", "security")
