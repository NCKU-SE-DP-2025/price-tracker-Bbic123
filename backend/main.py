import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
import os
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text,
						create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


user_news_association_table = Table(
	"user_news_upvotes",
	Base.metadata,
	Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
	Column(
		"news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
	),
)

# from pydantic import BaseModel


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

# import os
from openai import OpenAI


# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

#
# def extract_search_keywords(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content


from urllib.parse import quote
# import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session


def add_new_news_article(news_data):
	"""
	add new to db
	:param news_data: news info
	:return:
	"""
	session = Session()
	session.add(NewsArticle(
		url=news_data["url"],
		title=news_data["title"],
		time=news_data["time"],
		content=" ".join(news_data["content"]),  # 將內容list轉換為字串
		summary=news_data["summary"],
		reason=news_data["reason"],
	))
	session.commit()
	session.close()


def get_new_info(search_term, is_initial=False):
	"""
	get new

	:param search_term:
	:param is_initial:
	:return:
	"""
	all_news_data = []
	# iterate pages to get more news data, not actually get all news data
	if is_initial:
		for page_number in range(1, 10):
			query_params = {
				"page": page_number,
				"id": f"search:{quote(search_term)}",
				"channelId": 2,
				"type": "searchword",
			}
			response = requests.get("https://udn.com/api/more", params=query_params)
			all_news_data.append(response.json()["lists"])

	else:
		query_params = {
			"page": 1,
			"id": f"search:{quote(search_term)}",
			"channelId": 2,
			"type": "searchword",
		}
		response = requests.get("https://udn.com/api/more", params=query_params)

		all_news_data = response.json()["lists"]
	return all_news_data

def fetch_relevant_price_news_and_store(is_initial=False):
	"""
	get new info

	:param is_initial:
	:return:
	"""
	search_results = get_new_info("價格", is_initial=is_initial)
	for result_item in search_results:
		list_title = result_item["title"]
		relevance_messages = [
			{
				"role": "system",
				"content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
			},
			{"role": "user", "content": f"{list_title}"},
		]
		ai_relevance_completion = OpenAI(api_key="xxx").chat.completions.create(
			model="gpt-3.5-turbo",
			messages=relevance_messages,
		)
		relevance = ai_relevance_completion.choices[0].message.content
		if relevance == "high":
			article_response = requests.get(result_item["titleLink"])
			parsed_article = BeautifulSoup(article_response.text, "html.parser")
			# 標題
			detail_title = parsed_article.find("h1", class_="article-content__title").text
			published_time = parsed_article.find("time", class_="article-content__time").text
			# 定位到包含文章内容的 <section>
			content_section = parsed_article.find("section", class_="article-content__editor")

			paragraphs = [
				paragraph_tag.text
				for paragraph_tag in content_section.find_all("p")
				if paragraph_tag.text.strip() != "" and "▪" not in paragraph_tag.text
			]
			detailed_news =  {
				"url": result_item["titleLink"],
				"title": detail_title,
				"time": published_time,
				"content": paragraphs,
			}
			summary_messages = [
				{
					"role": "system",
					"content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
				},
				{"role": "user", "content": " ".join(detailed_news["content"])},
			]

			summary_completion = OpenAI(api_key="xxx").chat.completions.create(
				model="gpt-3.5-turbo",
				messages=summary_messages,
			)
			summary_dict = summary_completion.choices[0].message.content
			summary_dict = json.loads(summary_dict)
			detailed_news["summary"] = summary_dict["影響"]
			detailed_news["reason"] = summary_dict["原因"]
			add_new_news_article(detailed_news)


@app.on_event("startup")
def start_scheduler():
	database_session = SessionLocal()
	if database_session.query(NewsArticle).count() == 0:
		# should change into simple factory pattern
		fetch_relevant_price_news_and_store()
	database_session.close()
	background_scheduler.add_job(fetch_relevant_price_news_and_store, "interval", minutes=100)
	background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
	background_scheduler.shutdown()


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def database_session_opener():
	database_session = Session(bind=engine)
	try:
		yield database_session
	finally:
		database_session.close()


def verify_password(plain_password, hashed_password):
	return password_context.verify(plain_password, hashed_password)


def check_user_password_is_correct(database_session, username, plain_password):
	user = database_session.query(User).filter(User.username == username).first()
	if not verify_password(plain_password, user.hashed_password):
		return False
	return user


def authenticate_user_token(
	access_token = Depends(oauth2_bearer_scheme),
	database_session = Depends(database_session_opener)
):
	token_payload = jwt.decode(access_token, '1892dhianiandowqd0n', algorithms=["HS256"])
	return database_session.query(User).filter(User.username == token_payload.get("sub")).first()


def create_access_token(base_claims, expires_delta=None):
	"""create access token"""
	to_encode = base_claims.copy()
	if expires_delta:
		expires_at_utc = datetime.utcnow() + expires_delta
	else:
		expires_at_utc = datetime.utcnow() + timedelta(minutes=15)
	to_encode.update({"exp": expires_at_utc})
	print(to_encode)
	encoded_jwt = jwt.encode(to_encode, '1892dhianiandowqd0n', algorithm="HS256")
	return encoded_jwt


@app.post("/api/v1/users/login")
async def login_for_access_token(
	form_data: OAuth2PasswordRequestForm = Depends(),
	database_session = Depends(database_session_opener),
):
	"""login"""
	user = check_user_password_is_correct(database_session, form_data.username, form_data.password)
	access_token = create_access_token(
		base_claims={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
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
	hashed_password = password_context.hash(user.password)
	database_user = User(username=user.username, hashed_password=hashed_password)
	database_session.add(database_user)
	database_session.commit()
	database_session.refresh(database_user)
	return database_user


@app.get("/api/v1/users/me")
def read_users_me(current_user=Depends(authenticate_user_token)):
	return {"username": current_user.username}


_id_counter = itertools.count(start=1000000)


def get_article_upvote_details(article_id, user_id, database_session):
	upvote_count = (
		database_session.query(user_news_association_table)
		.filter_by(news_articles_id=article_id)
		.count()
	)
	has_voted = False
	if user_id:
		has_voted = (
			database_session.query(user_news_association_table)
			.filter_by(news_articles_id=article_id, user_id=user_id)
			.first()
			is not None
		)
	return upvote_count, has_voted


@app.get("/api/v1/news/news")
def read_news(database_session=Depends(database_session_opener)):
	"""
	read new

	:param db:
	:return:
	"""
	news_articles = database_session.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
	articles_with_votes = []
	for article in news_articles:
		upvotes, upvoted = get_article_upvote_details(article.id, None, database_session)
		articles_with_votes.append(
			{**article.__dict__, "upvotes": upvotes, "is_upvoted": upvoted}
		)
	return articles_with_votes


@app.get("/api/v1/news/user_news")
def read_user_news(
	database_session=Depends(database_session_opener),
	current_user=Depends(authenticate_user_token),
):
	"""
	read user new

	:param db:
	:param u:
	:return:
	"""
	news_articles = database_session.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
	articles_with_votes = []
	for article in news_articles:
		upvotes, upvoted = get_article_upvote_details(article.id, current_user.id, database_session)
		articles_with_votes.append(
			{
				**article.__dict__,
				"upvotes": upvotes,
				"is_upvoted": upvoted,
			}
		)
	return articles_with_votes

class PromptRequest(BaseModel):
	prompt: str

@app.post("/api/v1/news/search_news")
async def search_news(prompt_request: PromptRequest):
	user_prompt = prompt_request.prompt
	news_articles = []
	messages = [
		{
			"role": "system",
			"content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
		},
		{
			"role": "user",
			"content": f"{user_prompt}"
		},
	]

	keyword_completion = OpenAI(api_key="xxx").chat.completions.create(
		model="gpt-3.5-turbo",
		messages=messages,
	)
	keywords = keyword_completion.choices[0].message.content
	# should change into simple factory pattern
	search_results = get_new_info(keywords, is_initial=False)
	for result in search_results:
		try:
			article_response = requests.get(result["titleLink"])
			parsed_article = BeautifulSoup(article_response.text, "html.parser")
			# 標題
			detail_title = parsed_article.find("h1", class_="article-content__title").text
			published_time = parsed_article.find("time", class_="article-content__time").text
			# 定位到包含文章内容的 <section>
			content_section = parsed_article.find("section", class_="article-content__editor")

			paragraphs = [
				paragraph_tag.text
				for paragraph_tag in content_section.find_all("p")
				if paragraph_tag.text.strip() != "" and "▪" not in paragraph_tag.text
			]
			article_payload = {
				"url": result["titleLink"],
				"title": detail_title,
				"time": published_time,
				"content": paragraphs,
			}
			article_payload["content"] = " ".join(article_payload["content"])
			article_payload["id"] = next(_id_counter)
			news_articles.append(article_payload)
		except Exception as exc:
			print(exc)
	return sorted(news_articles, key=lambda x: x["time"], reverse=True)

class NewsSummaryRequestSchema(BaseModel):
	content: str

@app.post("/api/v1/news/news_summary")
async def news_summary(
	summary_request: NewsSummaryRequestSchema,
	# current_user=Depends(authenticate_user_token),
):
	summary_response = {}
	messages = [
		{
			"role": "system",
			"content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
		},
		{
			"role": "user",
			"content": f"{summary_request.content}"
		},
	]

	summary_completion = OpenAI(api_key="xxx").chat.completions.create(
		model="gpt-3.5-turbo",
		messages=messages,
	)
	summary_text = summary_completion.choices[0].message.content
	if summary_text:
		summary_dict = json.loads(summary_text)
		summary_response["summary"] = summary_dict["影響"]
		summary_response["reason"] = summary_dict["原因"]
	return summary_response


@app.post("/api/v1/news/{article_id}/upvote")
def upvote_article(
	article_id,
	database_session=Depends(database_session_opener),
	current_user=Depends(authenticate_user_token),
):
	message = toggle_upvote(article_id, current_user.id, database_session)
	return {"message": message}


def toggle_upvote(article_id, user_id, database_session):
	existing_upvote = database_session.execute(
		select(user_news_association_table).where(
			user_news_association_table.c.news_articles_id == article_id,
			user_news_association_table.c.user_id == user_id,
		)
	).scalar()

	if existing_upvote:
		delete_stmt = delete(user_news_association_table).where(
			user_news_association_table.c.news_articles_id == article_id,
			user_news_association_table.c.user_id == user_id,
		)
		database_session.execute(delete_stmt)
		database_session.commit()
		return "Upvote removed"
	else:
		insert_stmt = insert(user_news_association_table).values(
			news_articles_id=article_id, user_id=user_id
		)
		database_session.execute(insert_stmt)
		database_session.commit()
		return "Article upvoted"


def news_exists(article_id, database_session):
	return database_session.query(NewsArticle).filter_by(id=article_id).first() is not None


@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
	category_name=Query(None), commodity_name=Query(None)
):
	return requests.get(
		"https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
		params={"CategoryName": category_name, "Name": commodity_name},
	).json()
