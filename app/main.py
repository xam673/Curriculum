from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app import models  # noqa: F401  (registers tables)
from app.database import Base, engine
from app.exceptions import AppError
from app.routers import auth, courses, students

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CUrriculum API", version="0.2.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Turns business-logic errors into JSON responses with the right status code."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(students.router)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok"}