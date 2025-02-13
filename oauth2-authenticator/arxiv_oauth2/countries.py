
"""arXiv category routes."""
import pycountry
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db.models import Category

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/countries", tags=["metadata"])

class CountryModel(BaseModel):
    id: str
    name: str
    numeric_id: str
    official_name: str

country_dict = [{"id": country.alpha_2, "name": country.name, "numeric_id": country.numeric, "official_name": getattr(country, "official_name", "")} for country in pycountry.countries]

@router.get('/')
async def list_countries(
        response: Response,
        _sort: Optional[str] = Query("name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        name: Optional[str] = Query(""),
    ) -> List[CountryModel]:
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    result = country_dict.copy()

    if name:
        result = [ country for country in country_dict if country["name"].find(name) >= 0 ]

    if _order == "DESC":
        result = sorted(result, key=lambda country: country[_sort])
    else:
        result = sorted(result, key=lambda country: country[_sort])

    response.headers['X-Total-Count'] = str(len(result))
    return [CountryModel.model_validate(country) for country in result[_start:_end]]


@router.get('/alpha_2/{alpha_2}')
async def get_country(
        response: Response,
        alpha_2: str,
    ) -> CountryModel:
    if len(alpha_2) != 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,)

    alpha_2 = alpha_2.upper()
    result = [country for country in country_dict if country["id"] == alpha_2]
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,)
    return CountryModel.model_validate(result[0])
