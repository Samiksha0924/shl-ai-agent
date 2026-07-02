
from app.core.env import *
from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(

    title="SHL Assessment Recommendation API",

    version="1.0",

    description="AI-powered assessment recommendation system.",

)

app.include_router(router)