import requests
from fastapi import APIRouter, Query


router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/necessities-price")
def get_necessities_prices(
    category_name: str = Query(None),
    commodity_name: str = Query(None),
):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={
            "CategoryName": category_name,
            "Name": commodity_name,
        },
    ).json()
