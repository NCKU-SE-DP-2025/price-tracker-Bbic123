import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.service import token_auth_service
from src.database import database
from src.news.constants import (
    EXTRACT_NEWS_KEYWORDS_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
)
from src.news.schemas import (
    PromptRequest,
    NewsSummaryRequestSchema,
)
from src.news.service import (
    ai_service,
    news_service,
    news_vote_service,
    GetVotedArticles,
)


router = APIRouter(prefix="/news", tags=["news"])


@router.get("/news")
def get_news(
    database_session: Session = Depends(database.get_session),
):
    """
    get new
    """
    service = GetVotedArticles(database_session)
    return service.get_all_articles(current_user_id=None)


@router.get("/user_news")
def get_user_news(
    database_session: Session = Depends(database.get_session),
    current_user=Depends(
        token_auth_service.authenticate_user_token
    ),
):
    """
    get user new
    """
    service = GetVotedArticles(database_session)
    return service.get_all_articles(
        current_user_id=current_user.id,
    )


@router.post("/search_news")
async def search_news(prompt_request: PromptRequest):
    user_prompt = prompt_request.prompt
    keywords = ai_service.ai_completion(
        EXTRACT_NEWS_KEYWORDS_SYSTEM_PROMPT,
        user_prompt,
    )
    news_articles = news_service.search_news_by_keywords(keywords)
    return news_articles


@router.post("/news_summary")
async def news_summary(summary_request: NewsSummaryRequestSchema):
    summary_response: dict = {}
    summary_text = ai_service.ai_completion(
        SUMMARY_SYSTEM_PROMPT,
        f"{summary_request.content}",
    )
    if summary_text:
        summary_dict = json.loads(summary_text)
        summary_response["summary"] = summary_dict["影響"]
        summary_response["reason"] = summary_dict["原因"]
    return summary_response


@router.post("/{article_id}/upvote")
def upvote_article(
    article_id: int,
    database_session: Session = Depends(database.get_session),
    current_user=Depends(
        token_auth_service.authenticate_user_token
    ),
):
    message = news_vote_service.toggle_upvote(
        article_id,
        current_user.id,
        database_session,
    )
    return {"message": message}
