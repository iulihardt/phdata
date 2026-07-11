from __future__ import annotations

import logging
import os
import re
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.endpoints import router as api_router
from api.web import router as web_router
from services.imputer import KNNImputerService
from services.predictor import PredictionService
from utils.loader import load_demographics, load_features, load_model

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all resources once at startup so every request pays zero I/O cost."""
    logger.info("Loading ML model …")
    model = load_model("model/model.pkl")
    logger.info("Model loaded.")

    logger.info("Loading model feature list …")
    model_features = load_features("model/model_features.json")
    logger.info("Feature list loaded: %s", model_features)

    logger.info("Loading demographics data …")
    demographics = load_demographics("data/zipcode_demographics.csv")
    logger.info("Demographics loaded: %d zipcodes.", len(demographics))

    logger.info("Fitting KNN imputer …")
    imputer = KNNImputerService()
    imputer.fit("data/kc_house_data.csv")
    logger.info("KNN imputer fitted and ready.")

    app.state.prediction_service = PredictionService(
        model=model,
        model_features=model_features,
        demographics=demographics,
        imputer=imputer,
    )

    logger.info("All resources loaded. API is ready to serve requests.")
    yield


app = FastAPI(
    title="Sound Realty Price Predictor",
    description="Predicts home values in the Seattle area using ML with KNN imputation for missing data.",
    version="1.0.0",
    lifespan=lifespan,
)


_VALID_JSON_VALUE = re.compile(
    r'^("|\d|-|true|false|null|\[|\{)'
)


def _find_all_invalid_fields(raw_body: bytes) -> list[dict]:
    """Scan raw body text for all fields with values that are not valid JSON tokens."""
    try:
        text = raw_body.decode("utf-8") if isinstance(raw_body, bytes) else raw_body
    except (UnicodeDecodeError, AttributeError):
        return [{"field": "unknown", "message": "JSON decode error"}]

    errors = []
    for match in re.finditer(r'"(\w+)"\s*:\s*(.+)', text):
        field_name = match.group(1)
        raw_value = match.group(2).rstrip().rstrip(",")
        if not _VALID_JSON_VALUE.match(raw_value.strip()):
            errors.append({
                "field": field_name,
                "message": f"Invalid value: {raw_value.strip()}",
            })

    return errors or [{"field": "unknown", "message": "JSON decode error"}]


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a clean, consistent error format for all validation failures."""
    errors = []
    for err in exc.errors():
        loc_parts = [p for p in err["loc"] if p != "body"]

        if err.get("type") == "json_invalid" and exc.body:
            errors.extend(_find_all_invalid_fields(exc.body))
            break
        else:
            field = ".".join(str(p) for p in loc_parts)
            errors.append({"field": field, "message": err["msg"]})

    return JSONResponse(status_code=422, content={"detail": errors})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch any unhandled exception, log traceback, and return a clean 500 JSON."""
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    logger.debug("Traceback:\n%s", traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every request with endpoint and timing; catch unhandled exceptions."""
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error(
            "Unhandled exception on %s %s (%.1fms): %s",
            request.method,
            request.url.path,
            elapsed_ms,
            exc,
        )
        logger.debug("Traceback:\n%s", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "method=%s path=%s status=%d duration_ms=%.1f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

_BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(_BASE_DIR / "templates"))
app.state.templates = templates
app.mount("/static", StaticFiles(directory=str(_BASE_DIR / "static")), name="static")
app.include_router(web_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)