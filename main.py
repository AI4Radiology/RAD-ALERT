

import os
from fastapi import FastAPI
from dotenv import load_dotenv
from api.settings import settings


load_dotenv()


app = FastAPI(title="Rad-Alert API")


from api.worker import start_worker
from api.routes import router as api_router


app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    start_worker()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",     
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=True
    )
