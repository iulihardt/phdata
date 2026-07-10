import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.endpoints import router as api_router
from services.imputer import KNNImputerService
from services.predictor import PredictionService
from utils.loader import load_demographics, load_features, load_model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a clean, consistent error format for all validation failures."""
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        errors.append({"field": field, "message": err["msg"]})
    return JSONResponse(status_code=422, content={"detail": errors})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)