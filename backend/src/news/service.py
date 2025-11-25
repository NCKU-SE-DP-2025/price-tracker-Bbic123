import json
import itertools

from main import OpenAI
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session
from src.crawler.udn_crawler import UDNCrawler
from src.crawler.crawler_base import NewsWithSummary

from src.database import database
from src.news.constants import (
    PRICE_RELEVANCE_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
)
from src.news.models import NewsArticle, user_news_association_table


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
    

class NewsVoteService:
    def __init__(self, association_table=user_news_association_table):
        self.association_table = association_table

    def __user_vote_query_existing(
        self,
        article_id: int,
        user_id: int,
        database_session: Session,
    ):
        return (
            database_session.query(self.association_table)
            .filter_by(
                news_articles_id=article_id,
                user_id=user_id,
            )
            .first()
        )

    def get_article_upvote_details(
        self,
        article_id,
        user_id,
        database_session: Session,
    ):
        upvote_count = (
            database_session.query(self.association_table)
            .filter_by(news_articles_id=article_id)
            .count()
        )
        has_voted = (
            self.__user_vote_query_existing(
                article_id,
                user_id,
                database_session,
            )
            is not None
            if user_id
            else False
        )
        return upvote_count, has_voted

    def toggle_upvote(
        self,
        article_id,
        user_id,
        database_session: Session,
    ):
        existing_upvote = self.__user_vote_query_existing(
            article_id,
            user_id,
            database_session,
        )
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
                user_id=user_id,
            )
            database_session.execute(insert_statement)
            database_session.commit()
            return "Article upvoted"


class GetVotedArticles:
    def __init__(self, database_session: Session):
        self.database_session = database_session

    def get_all_articles(self, current_user_id):
        news_articles = (
            self.database_session.query(NewsArticle)
            .order_by(NewsArticle.time.desc())
            .all()
        )
        articles_with_votes = []
        for article in news_articles:
            upvotes, upvoted = news_vote_service.get_article_upvote_details(
                article.id,
                current_user_id,
                self.database_session,
            )
            articles_with_votes.append(
                {
                    **article.__dict__,
                    "upvotes": upvotes,
                    "is_upvoted": upvoted,
                }
            )
        return articles_with_votes


class NewsService(AIService):
    def __init__(
        self,
        udn_crawler: UDNCrawler,
        api_key: str = "xxx",
        model: str = "gpt-3.5-turbo",
        database_session: Session = database.session,
    ):
        super().__init__(api_key=api_key, model=model)
        self.udn_crawler = udn_crawler
        self.database_session = database_session

    def get_new_info(self, search_term: str, is_initial: bool = False):
        if is_initial:
            return self.udn_crawler.startup(search_term)
        return self.udn_crawler.get_headline(search_term, page=1)

    def fetch_relevant_price_news_and_store(
        self,
        is_initial: bool = False,
    ):
        search_results = self.get_new_info("價格", is_initial=is_initial)
        for headline in search_results:
            list_title = headline.title
            if (
                self.ai_completion(
                    PRICE_RELEVANCE_SYSTEM_PROMPT,
                    list_title,
                )
                != "high"
            ):
                continue

            detailed_news = self.udn_crawler.parse(headline.url)
            summary_text = self.ai_completion(
                SUMMARY_SYSTEM_PROMPT,
                detailed_news.content,
            )
            summary_dict = json.loads(summary_text)

            news_with_summary = NewsWithSummary(
                url = detailed_news.url,
                title = detailed_news.title,
                time = detailed_news.time,
                content = detailed_news.content,
                summary = summary_dict["影響"],
                reason = summary_dict["原因"],
            )
            self.udn_crawler.save(news_with_summary, self.database_session)

    def search_news_by_keywords(self, keywords: str) -> list[dict]:
        """
        給關鍵字，回傳整理好的新聞列表（已經爬完文章、排好時間順序）
        """
        search_results = self.get_new_info(keywords, is_initial=False)
        news_articles: list[dict] = []

        for headline in search_results:
            try:
                article_payload = self.udn_crawler.parse(headline.url)
                article_payload = {
                    "url": article_payload.url,
                    "title": article_payload.title,
                    "time": article_payload.time,
                    "content": article_payload.content,
                    "id": next(_id_counter),
                }
                news_articles.append(article_payload)
            except Exception as exc:
                print(exc)

        return sorted(
            news_articles,
            key=lambda x: x["time"],
            reverse=True,
        )


ai_service = AIService()
udn_crawler = UDNCrawler()
news_vote_service = NewsVoteService()
news_service = NewsService(udn_crawler, database_session=database.session)
_id_counter = itertools.count(start=1000000)
