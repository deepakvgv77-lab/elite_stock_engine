from icalendar import Calendar, Event
from datetime import datetime
from typing import List
from app.events_actions.calendars import CalendarService

class ICSScheduler:
    def export(self, days: int = 30) -> bytes:
        cal = Calendar()
        cs = CalendarService()
        events = cs.get_dividends(days) + cs.get_agm(days)
        for d in events:
            ev = Event()
            summary = f"{d.get('symbol', '')} "
            if 'amount' in d:
                summary += f"Dividend {d['amount']}"
            else:
                summary += "AGM/EGM"
            ev.add("summary", summary)
            event_date = d.get('ex_date') or d.get('agm_date')
            ev.add("dtstart", datetime.fromisoformat(event_date))
            cal.add_component(ev)
        return cal.to_ical()
