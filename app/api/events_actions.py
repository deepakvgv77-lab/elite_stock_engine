from fastapi import APIRouter, Query, Body
from typing import List, Dict
from app.events_actions.corporate_actions import CorporateActionsService
from app.events_actions.calendars import CalendarService
from app.events_actions.catalyst import CatalystCardsService
from app.events_actions.ics_export import ICSScheduler
from fastapi.responses import Response

router = APIRouter(prefix="/api/v4/events", tags=["Events_Actions"])
cas = CorporateActionsService()
cs = CalendarService()
ccs = CatalystCardsService()
ics = ICSScheduler()

@router.get("/actions", response_model=List[Dict])
def actions():
    return cas.fetch_actions()

@router.get("/dividends", response_model=List[Dict])
def dividends(days: int = Query(7)):
    return cs.get_dividends(days)

@router.get("/agm", response_model=List[Dict])
def agm(days: int = Query(7)):
    return cs.get_agm(days)

@router.post("/catalyst", response_model=Dict)
def catalyst(payload: Dict = Body(...)):
    return ccs.generate_card(payload["symbol"], payload["event_id"])

@router.get("/export/ics")
def export_ics(days: int = Query(30)):
    return Response(content=ics.export(days), media_type="text/calendar")
