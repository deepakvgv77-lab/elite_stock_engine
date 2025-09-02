from fastapi import APIRouter
from app.ui.theme import router as theme_router

router = APIRouter()
router.include_router(theme_router, prefix="/theme", tags=["UI"])
