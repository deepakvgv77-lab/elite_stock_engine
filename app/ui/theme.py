from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/theme")
async def get_theme(dark: bool = Query(False)):
    if dark:
        return {"theme": "dark", "colors": {"background": "#121212", "text": "#ffffff"}}
    else:
        return {"theme": "light", "colors": {"background": "#ffffff", "text": "#000000"}}
