from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models  # noqa: F401  (registers tables)
from app.database import Base, engine
from app.routers import auth, courses

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CUrriculum API", version="0.1.0")

# Lets the frontend (running on another port/domain) call this API
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(courses.router)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok"}