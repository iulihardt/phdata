from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import router as api_router
from services.imputer import KNNImputerService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Fit the KNN imputer once at startup so it is ready for every request."""
    imputer = KNNImputerService()
    imputer.fit("data/kc_house_data.csv")
    app.state.imputer = imputer
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