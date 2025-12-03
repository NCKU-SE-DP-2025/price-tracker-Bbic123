import json
import itertools

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session
from urllib.parse import quote

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
                all_news_data.extend(
                    self.fetch_udn_page(search_term, page_number)
                )
            return all_news_data
        return self.fetch_udn_page(search_term, 1)

    def parse_udn_article(self, article_url: str) -> dict:
        """
        parse udn article
        """
        article_response = requests.get(article_url)
        parsed_article = BeautifulSoup(
            article_response.text,
            "html.parser",
        )

        detail_title = parsed_article.find(
            "h1",
            class_="article-content__title",
        ).text
        published_time = parsed_article.find(
            "time",
            class_="article-content__time",
        ).text
        content_section = parsed_article.find(
            "section",
            class_="article-content__editor",
        )

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


class NewsArticleRepository:
    def __init__(self, session_factory):
        self.Session = session_factory

    def add_new_news_article(self, news_data: dict):
        session: Session = self.Session()
        session.add(
            NewsArticle(
                url=news_data["url"],
                title=news_data["title"],
                time=news_data["time"],
                content=" ".join(news_data["content"]),
                summary=news_data["summary"],
                reason=news_data["reason"],
            )
        )
        session.commit()
        session.close()


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
        udn_client: UdnNewsSourceService,
        news_repo: NewsArticleRepository,
        api_key: str = "xxx",
        model: str = "gpt-3.5-turbo",
    ):
        super().__init__(api_key=api_key, model=model)
        self.udn_client = udn_client
        self.news_repo = news_repo

    def get_new_info(self, search_term: str, is_initial: bool = False):
        return self.udn_client.fetch_news_list(
            search_term,
            is_initial=is_initial,
        )

    def fetch_relevant_price_news_and_store(
        self,
        is_initial: bool = False,
    ):
        search_results = self.get_new_info("價格", is_initial=is_initial)
        for result_item in search_results:
            list_title = result_item["title"]
            if (
                self.ai_completion(
                    PRICE_RELEVANCE_SYSTEM_PROMPT,
                    list_title,
                )
                != "high"
            ):
                continue

            detailed_news = self.udn_client.parse_udn_article(
                result_item["titleLink"]
            )
            summary_text = self.ai_completion(
                SUMMARY_SYSTEM_PROMPT,
                " ".join(detailed_news["content"]),
            )
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
                article_payload = self.udn_client.parse_udn_article(
                    result["titleLink"]
                )
                article_payload["content"] = " ".join(
                    article_payload["content"]
                )
                article_payload["id"] = next(_id_counter)
                news_articles.append(article_payload)
            except Exception as exc:
                print(exc)

        return sorted(
            news_articles,
            key=lambda x: x["time"],
            reverse=True,
        )


ai_service = AIService()
udn_client = UdnNewsSourceService()
news_repo = NewsArticleRepository(database.SessionLocal)
news_vote_service = NewsVoteService()
news_service = NewsService(udn_client, news_repo)
_id_counter = itertools.count(start=1000000)
