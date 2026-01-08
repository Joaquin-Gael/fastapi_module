from fastapi import APIRouter
from server.routes.auth import router as router_auth
from server.routes.user import router as router_user
from server.routes.docs import router as router_docs
from server.routes.admin import router as router_admin

router_main = APIRouter()
router_main.include_router(router_auth)
router_main.include_router(router_user)
router_main.include_router(router_docs)
router_main.include_router(router_admin)