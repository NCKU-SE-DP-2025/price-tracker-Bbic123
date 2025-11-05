import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import itertools
from sqlalchemy import delete, insert, select, Column, ForeignKey, Integer, String, Table, Text, create_engine
from sqlalchemy.orm import Session, sessionmaker, relationship
from typing import List, Optional
import requests
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy.ext.declarative import declarative_base
from openai import OpenAI
from urllib.parse import quote
from bs4 import BeautifulSoup

Base = declarative_base()

user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id"),
        primary_key = True
    ),
    Column(
        "news_articles_id",
        Integer,
        ForeignKey("news_articles.id"),
        primary_key = True
    ),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )


engine = create_engine("sqlite:///news_database.db", echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def database_session_opener():
    database_session = Session(bind=engine)
    try:
        yield database_session
    finally:
        database_session.close()


# ==========================
# Auth: Password / JWT / Login / Token Auth
# ==========================


class PasswordService:
    def __init__(self):
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, plain_password: str) -> str:
        return self.password_context.hash(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.password_context.verify(plain_password, hashed_password)


class JwtTokenService:
    def __init__(
        self,
        secret_key: str = "1892dhianiandowqd0n",
        algorithm: str = "HS256",
        token_expire_minutes: int = 15,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes

    def create_access_token(self, base_claims: dict, expires_delta: Optional[timedelta] = None) -> str:
        """create access token"""
        to_encode = base_claims.copy()
        if expires_delta:
            expires_at_utc = datetime.utcnow() + expires_delta
        else:
            expires_at_utc = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expires_at_utc})
        print(to_encode)
        encoded_jwt = jwt.encode(to_encode, self.secret_key, self.algorithm)
        return encoded_jwt

    def decode_access_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])


class LoginService:
    def __init__(self, password_service: PasswordService):
        self.password_service = password_service
    
    def check_user_password_is_correct(self, database_session: Session, username: str, plain_password: str):
        user = database_session.query(User).filter(User.username == username).first()
        if not user:
            return False
        if not self.password_service.verify_password(plain_password, user.hashed_password):
            return False
        return user
    

class TokenAuthService:
    def __init__(self, jwt_token_service: JwtTokenService):
        self.jwt_token_service = jwt_token_service

    def authenticate_user_token(
        self,
        access_token = Depends(oauth2_bearer_scheme),
        database_session = Depends(database_session_opener)
    ):
        token_payload = self.jwt_token_service.decode_access_token(access_token)
        return database_session.query(User).filter(User.username == token_payload.get("sub")).first()

password_service = PasswordService()
jwt_token_service = JwtTokenService(
    secret_key = "1892dhianiandowqd0n",
    algorithm = "HS256",
    token_expire_minutes = 15,
)
login_service = LoginService(password_service)
token_auth_service = TokenAuthService(jwt_token_service)


# ==========================
# AI Service
# ==========================


class AIService:
    def __init__(self, api_key: str = "xxx", model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def build_message(self, role: str, content: str) -> dict:
        message = {
            "role": role,
            "content": content,
        }
        return message

    def ai_completion(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            self.build_message("system", system_prompt),
            self.build_message("user", user_prompt),
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content
    
ai_service = AIService()

# ==========================
# News Source
# ==========================


class UdnNewsSourceService:
    """
    udn news source service
    """
    def __init__(self):
        pass

    def fetch_udn_page(self, search_term, page_number: int):
        query_params = {
            "page": page_number,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=query_params)
        return response.json()["lists"]
    
    def fetch_news_list(self, search_term: str, is_initial: bool = False):
        if is_initial:
            all_news_data: list[dict] = []
            for page_number in range(1, 10):
                all_news_data.extend(self.fetch_udn_page(search_term, page_number))
            return all_news_data
        return self.fetch_udn_page(search_term, 1)
    
    def parse_udn_article(self, article_url: str) -> dict:
        """
        parse udn article

        :param article_url:
        :return:
        """
        article_response = requests.get(article_url)
        parsed_article = BeautifulSoup(article_response.text, "html.parser")
        # 標題
        detail_title = parsed_article.find("h1", class_="article-content__title").text
        published_time = parsed_article.find("time", class_="article-content__time").text
        # 定位到包含文章内容的 <section>
        content_section = parsed_article.find("section", class_="article-content__editor")

        paragraphs = [
            p.text
            for p in content_section.find_all("p")
            if p.text.strip() != "" and "▪" not in p.text
        ]

        return {
            "url": article_url,
            "title": detail_title,
            "time": published_time,
            "content": paragraphs,
        }
    
udn_client = UdnNewsSourceService()
    

# ==========================
# News Article Repository
# ==========================


class NewsArticleRepository:
    def __init__(self, session_factory):
        self.Session = session_factory

    def add_new_news_article(self, news_data: dict):
        session = self.Session()
        session.add(
            NewsArticle(
                url=news_data["url"],
                title=news_data["title"],
                time=news_data["time"],
                content=" ".join(news_data["content"]),  # 將內容list轉換為字串
                summary=news_data["summary"],
                reason=news_data["reason"],
            )
        )
        session.commit()
        session.close()

news_repo = NewsArticleRepository(SessionLocal)


# ==========================
# Vote Service
# ==========================


class NewsVoteService:
    def __init__(self, association_table = user_news_association_table):
        self.association_table = association_table

    def __user_vote_query_existing(self, article_id: int, user_id: int, database_session: Session):
        return database_session.query(self.association_table).filter_by(news_articles_id=article_id, user_id=user_id).first()

    def get_article_upvote_details(self, article_id, user_id, database_session: Session):
        upvote_count = (
            database_session.query(self.association_table)
            .filter_by(news_articles_id=article_id)
            .count()
        )
        has_voted = (
            self.__user_vote_query_existing(article_id, user_id, database_session) is not None
        ) if user_id else False
        return upvote_count, has_voted
    
    def toggle_upvote(self, article_id, user_id, database_session):
        existing_upvote = self.__user_vote_query_existing(article_id, user_id, database_session)

        if existing_upvote:
            delete_statement = delete(self.association_table).where(
                self.association_table.c.news_articles_id == article_id,
                self.association_table.c.user_id == user_id,
            )
            database_session.execute(delete_statement)
            database_session.commit()
            return "Upvote removed"
        else:
            insert_statement = insert(self.association_table).values(
                news_articles_id=article_id,
                user_id=user_id
            )
            database_session.execute(insert_statement)
            database_session.commit()
            return "Article upvoted"
        

class GetVotedArticles:
    def __init__(self, database_session):
        self.database_session = database_session

    def get_all_articles(self, current_user_id):
        news_articles = self.database_session.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
        articles_with_votes = []
        for article in news_articles:
            upvotes, upvoted = news_vote_service.get_article_upvote_details(article.id, current_user_id, self.database_session)
            articles_with_votes.append(
                {
                    **article.__dict__,
                    "upvotes": upvotes,
                    "is_upvoted": upvoted,
                }
            )
        return articles_with_votes

news_vote_service = NewsVoteService()
get_voted_articles_service = GetVotedArticles()


# ==========================
# Others
# ==========================


PRICE_RELEVANCE_SYSTEM_PROMPT = "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)"
SUMMARY_SYSTEM_PROMPT = "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})"
EXTRACT_NEWS_KEYWORDS_SYSTEM_PROMPT = "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)"

class NewsService(AIService):
    def __init__(
        self,
        udn_client: UdnNewsSourceService,
        news_repo: NewsArticleRepository,
    ):
        self.udn_client = udn_client
        self.news_repo = news_repo

    def get_new_info(self, search_term: str, is_initial: bool = False):
        return self.udn_client.fetch_news_list(search_term, is_initial=is_initial)
        
    def fetch_relevant_price_news_and_store(self, is_initial: bool = False):
        search_results = self.get_new_info("價格", is_initial=is_initial)
        for result_item in search_results:
            list_title = result_item["title"]

            if not self.ai_completion(PRICE_RELEVANCE_SYSTEM_PROMPT, list_title) == "high": # 評估相關性
                continue
            
            detailed_news = self.udn_client.parse_udn_article(result_item["titleLink"])  # 解析文章

            # 生成摘要和原因
            summary_text = self.ai_completion(SUMMARY_SYSTEM_PROMPT, " ".join(detailed_news["content"]))
            summary_dict = json.loads(summary_text)

            detailed_news["summary"] = summary_dict["影響"]
            detailed_news["reason"] = summary_dict["原因"]
            
            self.news_repo.add_new_news_article(detailed_news)

    def search_news_by_keywords(self, keywords: str) -> list[dict]:
        """
        給關鍵字，回傳整理好的新聞列表（已經爬完文章、排好時間順序）
        """
        search_results = self.get_new_info(keywords, is_initial=False)
        news_articles: list[dict] = []

        for result in search_results:
            try:
                article_payload = self.udn_client.parse_udn_article(result["titleLink"])
                article_payload["content"] = " ".join(article_payload["content"])
                article_payload["id"] = next(_id_counter)
                news_articles.append(article_payload)
            except Exception as exc:
                print(exc)

        # 依照時間排序（新到舊）
        return sorted(news_articles, key=lambda x: x["time"], reverse=True)

news_service = NewsService(udn_client, news_repo)


#########################################
#########################################


@app.on_event("startup")
def start_scheduler():
    database_session = SessionLocal()
    if database_session.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        news_service.fetch_relevant_price_news_and_store()
    database_session.close()
    background_scheduler.add_job(news_service.fetch_relevant_price_news_and_store, "interval", minutes=100)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()


@app.post("/api/v1/users/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    database_session = Depends(database_session_opener),
):
    """login"""
    user = login_service.check_user_password_is_correct(
        database_session,
        form_data.username,
        form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = jwt_token_service.create_access_token(
        base_claims = {"sub": str(user.username)},
        expires_delta = timedelta(minutes = 30)
    )
    return {"access_token": access_token, "token_type": "bearer"}


class UserAuthSchema(BaseModel):
    username: str
    password: str

@app.post("/api/v1/users/register")
def create_user(
    user: UserAuthSchema,
    database_session = Depends(database_session_opener),
):
    """create user"""
    hashed_password = password_service.hash_password(user.password)
    database_user = User(username=user.username, hashed_password=hashed_password)
    database_session.add(database_user)
    database_session.commit()
    database_session.refresh(database_user)
    return database_user


@app.get("/api/v1/users/me")
def get_users_me(current_user=Depends(token_auth_service.authenticate_user_token)):
    return {"username": current_user.username}


_id_counter = itertools.count(start=1000000)


@app.get("/api/v1/news/news")
def get_news(database_session=Depends(database_session_opener)):
    """
    get new

    :param db:
    :return:
    """
    service = GetVotedArticles(database_session)
    return service.get_all_articles(current_user_id=None)


@app.get("/api/v1/news/user_news")
def get_user_news(
    database_session=Depends(database_session_opener),
    current_user=Depends(token_auth_service.authenticate_user_token),
):
    """
    get user new

    :param db:
    :param u:
    :return:
    """
    service = GetVotedArticles(database_session)
    return service.get_all_articles(current_user_id=current_user.id)


class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/v1/news/search_news")
async def search_news(prompt_request: PromptRequest):
    user_prompt = prompt_request.prompt

    keywords = ai_service.ai_completion(
        EXTRACT_NEWS_KEYWORDS_SYSTEM_PROMPT,
        user_prompt
    )

    news_articles = news_service.search_news_by_keywords(keywords)

    return news_articles

class NewsSummaryRequestSchema(BaseModel):
    content: str

@app.post("/api/v1/news/news_summary")
async def news_summary(
    summary_request: NewsSummaryRequestSchema,
):
    summary_response = {}

    summary_text = ai_service.ai_completion(
        SUMMARY_SYSTEM_PROMPT,
        f"{summary_request.content}"
    )

    if summary_text:
        summary_dict = json.loads(summary_text)
        summary_response["summary"] = summary_dict["影響"]
        summary_response["reason"] = summary_dict["原因"]
    return summary_response


@app.post("/api/v1/news/{article_id}/upvote")
def upvote_article(
    article_id,
    database_session=Depends(database_session_opener),
    current_user=Depends(token_auth_service.authenticate_user_token),
):
    message = news_vote_service.toggle_upvote(article_id, current_user.id, database_session)
    return {"message": message}


@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
    category_name=Query(None), commodity_name=Query(None)
):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category_name, "Name": commodity_name},
    ).json()
