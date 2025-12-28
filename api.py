import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import Paper, EconBizResponse, SearchHits
import logging 

logger = logging.getLogger(__name__)


BASE_URL = "https://api.econbiz.de/v1/search"
DEFAULT_SIZE = 10

async def search(query: str, highlight: bool =True, sort: str ="date desc",  from_result: int=1, size: int=DEFAULT_SIZE, facets: str="language person subject type_genre isPartOf", save_response: bool=True) -> Optional[EconBizResponse]:
    logger.info(f"Searching for: {query}")
    logger.info(f"From position: {from_result}, Size: {size}")
  
    params = {
        "q": query,
        "highlight": highlight,
        "sort": sort,
        "ff": 'source:"econstor"', 
        "from": from_result,
        "size": size,
        "facets": facets
        }

    logger.info("Making API request")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params = params, timeout = 30)
            response.raise_for_status()
        except httpx.RequestError as e:
            logger.error(f"Error making API request: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occured: {e}")
            return None
    
        raw_data = response.json()
    
    try: 
        # Convert raw JSON to pydantic model 
        econbiz_response = EconBizResponse(hits=SearchHits(total=raw_data['hits']['total'],
        hits=[Paper(**paper) for paper in raw_data['hits']['hits']]),
        facets=raw_data.get('facets'),
        query=query,
        search_params=params
        )

        if save_response:
                # Await async save method from models.py 
                await _save_response(econbiz_response, query)

        papers = econbiz_response.get_papers()
        pdf_urls = econbiz_response.get_pdf_urls()

        logger.info(f"Found {econbiz_response.hits.total} total results")
        logger.info(f"Retrieved {len(papers)} papers")
        logger.info(f"Found {len(pdf_urls)} PDFs:")

        for paper_id, url in pdf_urls:
            logger.info(f" {paper_id}, {url}")

        return econbiz_response

    except Exception as e:
        logger.error(f"Error processing response data: {e}")
        return None  



async def _save_response(response: EconBizResponse, query: str)-> None:

    safe_query = query.replace(" ", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"response_{safe_query}_{timestamp}.json"
    filepath = Path("saved_responses")/filename

    # Await the async method from EconBizResponse 
    await response.save(filepath)
    logger.info(f"Response saved to: {filepath}")     