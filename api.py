from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from unicorngo_scraper import scrape_unicorngo_product


app = FastAPI(title="Sellout AI Unicorn Parser", version="1.0.0")


class ParseRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/parse")
def parse_product(payload: ParseRequest) -> Dict[str, Any]:
    try:
        return scrape_unicorngo_product(str(payload.url))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
