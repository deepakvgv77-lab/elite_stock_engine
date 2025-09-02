from fastapi import APIRouter, Body
from typing import Dict, List
from .screener import MFScreener, ETFScreener
from .metrics import Attribution
from .overlap import OverlapChecker

router = APIRouter(prefix="/api/v3/mf_etf", tags=["MF_ETF"])
mf = MFScreener()
etf = ETFScreener()
attrib = Attribution()
overlap = OverlapChecker()

@router.post("/mf/screen")
def mf_screen(filters: Dict = Body(...)):
    return mf.run(filters)

@router.post("/etf/screen")
def etf_screen(filters: Dict = Body(...)):
    return etf.run(filters)

@router.get("/mf/attribution")
def mf_attr(fid: int):
    return attrib.style(fid)

@router.post("/overlap")
def check_overlap(fids: List[int] = Body(...)):
    return overlap.funds(fids)
