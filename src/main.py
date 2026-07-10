import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import router as api_router
from services.imputer import KNNImputerService
from utils.loader import load_demographics, load_features, load_model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all resources once at startup so every request pays zero I/O cost."""
    logger.info("Loading ML model …")
    app.state.model = load_model("model/model.pkl")
    logger.info("Model loaded.")

    logger.info("Loading model feature list …")
    app.state.model_features = load_features("model/model_features.json")
    logger.info("Feature list loaded: %s", app.state.model_features)

    logger.info("Loading demographics data …")
    app.state.demographics = load_demographics("data/zipcode_demographics.csv")
    logger.info("Demographics loaded: %d zipcodes.", len(app.state.demographics))

    logger.info("Fitting KNN imputer …")
    imputer = KNNImputerService()
    imputer.fit("data/kc_house_data.csv")
    app.state.imputer = imputer
    logger.info("KNN imputer fitted and ready.")

    logger.info("All resources loaded. API is ready to serve requests.")
    yield


app = FastAPI(lifespan=lifespan)

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