from requests import Response
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from urllib.parse import quote
import requests

from .base import NewsCrawlerBase, Headline, News, NewsWithSummary
from src.news.models import NewsArticle

class UDNCrawler(NewsCrawlerBase):
    CHANNEL_ID = 2

    def __init__(self, timeout: int = 5) -> None:
        self.news_website_url = "https://udn.com/api/more"
        self.timeout = timeout

    def startup(self, search_term: str) -> list[Headline]:
        """
        Initializes the application by fetching news headlines for a given search term across multiple pages.
        This method is typically called at the beginning of the program when there is no data available,
        hence it fetches headlines from the first 10 pages.

        :param search_term: The term to search for in news headlines.
        :return: A list of Headline namedtuples containing the title and URL of news articles.
        :rtype: list[Headline]
        """
        return self.get_headline(search_term, page=(1, 10))

    def get_headline(
        self,
        search_term: str,
        page: int | tuple[int, int],
    ) -> list[Headline]:
        page_range = range(*page) if isinstance(page, tuple) else [page]
        headlines: list[Headline] = []
        for page_number in page_range:
            headlines.extend(self._fetch_news(page_number, search_term))
        return headlines

    def _fetch_news(self, page: int, search_term: str) -> list[Headline]:
        params = self._create_search_params(page, search_term)
        response = self._perform_request(params=params)
        return self._parse_headlines(response)

    def _create_search_params(self, page: int, search_term: str) -> dict:
        query_params = {
            "page": page,
            "id": f"search:{quote(search_term)}",
            "channelId": self.CHANNEL_ID,
            "type": "searchword",
        }
        return query_params

    def _perform_request(self, url: str | None = None, params: dict | None = None) -> Response:
        target_url = url or self.news_website_url
        response = requests.get(
            target_url,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    @staticmethod
    def _parse_headlines(response: Response) -> list[Headline]:
        news_data = response.json().get("lists", [])
        headlines: list[Headline] = []
        for item in news_data:
            title = item.get("title", "").strip()
            url = item.get("titleLink", "").strip()
            if title and url:
                headlines.append(Headline(title=title, url=url))
        return headlines

    def parse(self, url: str) -> News:
        response = self._perform_request(url=url)
        soup = BeautifulSoup(response.text, "html.parser")
        return self._extract_news(soup, url)

    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
        detail_title = soup.find(
            "h1",
            class_="article-content__title",
        ).text
        published_time = soup.find(
            "time",
            class_="article-content__time",
        ).text
        content_section = soup.find(
            "section",
            class_="article-content__editor",
        )

        paragraphs = [
            p.text
            for p in content_section.find_all("p")
            if p.text.strip() != "" and "▪" not in p.text
        ]

        return News(
            url = url,
            title = detail_title,
            time = published_time,
            content = " ".join(paragraphs),
        )

    def save(self, news_data: NewsWithSummary, db: Session):
        try:
            news_article = NewsArticle(
                url = news_data.url,
                title = news_data.title,
                time = news_data.time,
                content = news_data.content,
                summary = news_data.summary,
                reason = news_data.reason,
            )
            db.add(news_article)
            self._commit_changes(db)
        finally:
            db.close()

    @staticmethod
    def _commit_changes(db: Session):
        db.commit()