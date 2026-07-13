from fastapi import FastAPI

from backend.api.routes import router

from backend.api.learning import router as learning_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Atlas EV API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(learning_router)