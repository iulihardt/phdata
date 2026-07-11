from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

router = APIRouter()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_HEADERS = {"User-Agent": "sound-realty-price-predictor/1.0"}
NOMINATIM_TIMEOUT = 5.0


@router.get("/directmap", response_class=HTMLResponse)
async def directmap(request: Request):
    """Serve the interactive map page."""
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "directmap.html")


@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Proxy reverse-geocoding through Nominatim and return ZIP/city/state."""
    params = {
        "format": "jsonv2",
        "addressdetails": "1",
        "lat": str(lat),
        "lon": str(lon),
    }

    try:
        async with httpx.AsyncClient(timeout=NOMINATIM_TIMEOUT) as client:
            resp = await client.get(
                NOMINATIM_URL, params=params, headers=NOMINATIM_HEADERS
            )
            resp.raise_for_status()
    except httpx.TimeoutException:
        logger.warning("Nominatim timeout for lat=%s lon=%s", lat, lon)
        raise HTTPException(status_code=502, detail="Geocoding service timeout")
    except httpx.HTTPStatusError as exc:
        logger.warning("Nominatim HTTP %s for lat=%s lon=%s", exc.response.status_code, lat, lon)
        raise HTTPException(status_code=502, detail="Geocoding service error")
    except httpx.HTTPError as exc:
        logger.warning("Nominatim request failed for lat=%s lon=%s: %s", lat, lon, exc)
        raise HTTPException(status_code=502, detail="Geocoding service unavailable")

    data = resp.json()
    address = data.get("address", {})

    zipcode = address.get("postcode")
    if not zipcode:
        raise HTTPException(
            status_code=404,
            detail="No ZIP code found for this location",
        )

    city = address.get("city") or address.get("town") or address.get("village") or ""
    state = address.get("state", "")

    return {
        "zipcode": zipcode,
        "city": city,
        "state": state,
        "lat": lat,
        "lon": lon,
    }
