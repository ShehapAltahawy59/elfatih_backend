from .users import router as users_router
from .auth import router as auth_router
from .admin import router as admin_router
from .posts import router as posts_router
from .devices import router as devices_router

__all__ = ["users_router", "auth_router", "admin_router", "posts_router", "devices_router"]
