from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import pytz
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="Simple Clock API", version="1.0.0")

# Enable CORS for the frontend served from any origin (static file hosting)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_timezone(tz_name: str) -> timezone:
    try:
        return pytz.timezone(tz_name)
    except Exception as exc:  # pragma: no cover - FastAPI will turn into error response
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {tz_name}") from exc


def _filter_timezones(query: Optional[str]) -> List[str]:
    timezones = sorted(pytz.common_timezones)
    if query:
        query_lower = query.lower()
        timezones = [tz for tz in timezones if query_lower in tz.lower()]
    return timezones


def _format_offset_label(offset: timedelta) -> str:
    total_minutes = int(offset.total_seconds() / 60)
    sign = "+" if total_minutes >= 0 else "-"
    abs_minutes = abs(total_minutes)
    hours, minutes = divmod(abs_minutes, 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


class TimezoneInfo(BaseModel):
    name: str
    utc_offset_hours: float
    utc_offset_label: str


def _build_timezone_info(tz_name: str, reference_utc: datetime) -> TimezoneInfo:
    tz = _get_timezone(tz_name)
    localized = reference_utc.astimezone(tz)
    offset = localized.utcoffset() or timedelta()
    offset_hours = offset.total_seconds() / 3600
    return TimezoneInfo(
        name=tz_name,
        utc_offset_hours=offset_hours,
        utc_offset_label=_format_offset_label(offset),
    )


def _extract_offset_metadata(dt: datetime) -> Tuple[float, str]:
    offset = dt.utcoffset() or timedelta()
    offset_hours = offset.total_seconds() / 3600
    return offset_hours, _format_offset_label(offset)


class LocalTimeRequest(BaseModel):
    timezone: str = Field(..., description="IANA timezone name detected or chosen by the user")
    offset_hours: float = Field(0, description="Offset to apply in hours (-24 to 24)")


class ConvertTimeRequest(BaseModel):
    from_timezone: str = Field(..., description="Source timezone (usually local)")
    to_timezone: str = Field(..., description="Target timezone selected by the user")
    offset_hours: float = Field(0, description="Offset to apply in hours (-24 to 24)")


class TimeResponse(BaseModel):
    timezone: str
    datetime_iso: str
    formatted: str
    offset_hours_applied: float
    utc_offset_hours: float
    utc_offset_label: str


@app.get("/api/timezones", response_model=List[str])
def list_timezones(query: Optional[str] = Query(None, description="Filter timezones by substring")) -> List[str]:
    return _filter_timezones(query)


@app.get("/api/timezones/details", response_model=List[TimezoneInfo])
def list_timezone_details(query: Optional[str] = Query(None, description="Filter timezones by substring")) -> List[TimezoneInfo]:
    reference_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
    timezones = _filter_timezones(query)
    return [_build_timezone_info(tz, reference_utc) for tz in timezones]


def _apply_offset(base_dt: datetime, offset_hours: float) -> datetime:
    return base_dt + timedelta(hours=offset_hours)


@app.post("/api/time/local", response_model=TimeResponse)
def get_local_time(request: LocalTimeRequest) -> TimeResponse:
    tz = _get_timezone(request.timezone)
    now = datetime.now(tz)
    shifted = _apply_offset(now, request.offset_hours)
    formatted = shifted.strftime("%Y-%m-%d %H:%M:%S %Z")
    offset_hours, offset_label = _extract_offset_metadata(shifted)
    return TimeResponse(
        timezone=request.timezone,
        datetime_iso=shifted.isoformat(),
        formatted=formatted,
        offset_hours_applied=request.offset_hours,
        utc_offset_hours=offset_hours,
        utc_offset_label=offset_label,
    )


@app.post("/api/time/convert", response_model=TimeResponse)
def convert_time(request: ConvertTimeRequest) -> TimeResponse:
    from_tz = _get_timezone(request.from_timezone)
    to_tz = _get_timezone(request.to_timezone)

    base_now = datetime.now(from_tz)
    shifted = _apply_offset(base_now, request.offset_hours)
    converted = shifted.astimezone(to_tz)
    formatted = converted.strftime("%Y-%m-%d %H:%M:%S %Z")
    offset_hours, offset_label = _extract_offset_metadata(converted)

    return TimeResponse(
        timezone=request.to_timezone,
        datetime_iso=converted.isoformat(),
        formatted=formatted,
        offset_hours_applied=request.offset_hours,
        utc_offset_hours=offset_hours,
        utc_offset_label=offset_label,
    )


@app.get("/api/health")
def healthcheck():
    return {"status": "ok"}


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    # Serve the static frontend directly from the same app for containerized deploys
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
