from typing import List, Dict
from app.core.database import db_manager
from .models import HoldingCreate

def create_holding(user_id:str, h:HoldingCreate) -> int:
    sql = """INSERT INTO portfolio(user_id,symbol,quantity,avg_price,added_at)
             VALUES(?,?,?,?,CURRENT_DATE)"""
    db_manager.execute_insert(sql, [user_id, h.symbol, h.quantity, h.avg_price])
    # Return inserted record id or count (simplified here)
    return 1

def list_holdings(user_id:str) -> List[Dict]:
    sql = "SELECT * FROM portfolio WHERE user_id=?"
    return db_manager.execute_query(sql, [user_id])

def delete_holding(user_id:str, hid:int):
    sql = "DELETE FROM portfolio WHERE user_id=? AND id=?"
    db_manager.execute_insert(sql, [user_id, hid])
