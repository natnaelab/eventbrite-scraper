from pydantic import BaseModel


class EventData(BaseModel):
    event_name: str
    date_time: dict[str, str]
    event_url: str
    location: str
    prices: list[dict[str, str]]
