import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from openai import OpenAI

from src.auth.router import router as auth_router
from src.database import database
from src.news.models import NewsArticle
from src.news.router import router as news_router
from src.news.service import news_service
from src.prices.router import router as prices_router

get_new_info = news_service.get_new_info

sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(prices_router, prefix="/api/v1")


@app.on_event("startup")
def start_scheduler():
    database.create_tables()

    database_session = database.SessionLocal()
    if database_session.query(NewsArticle).count() == 0:
        news_service.fetch_relevant_price_news_and_store()
    database_session.close()

    background_scheduler.add_job(
        news_service.fetch_relevant_price_news_and_store,
        "interval",
        minutes=100,
    )
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()
