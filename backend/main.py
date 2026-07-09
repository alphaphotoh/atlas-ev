from fastapi import FastAPI

from backend.api.routes import router

from backend.api.learning import router as learning_router

app = FastAPI(
    title="Atlas EV API",
    version="1.0.0"
)

app.include_router(router)
app.include_router(learning_router)