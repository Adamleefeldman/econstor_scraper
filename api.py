import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from models import Paper, EconBizResponse, SearchHits
import logging 

logger = logging.getLogger(__name__)


BASE_URL = "https://api.econbiz.de/v1/search"
DEFAULT_SIZE = 10


async def search(query: str, highlight: bool =True, sort: str ="date desc",  from_result: int=1, size: int=DEFAULT_SIZE, facets: str="language person subject type_genre isPartOf", save_response: bool=True) -> Optional[EconBizResponse]:
    logger.info(f"Searching for: {query}")
    logger.info(f"From position: {from_result}, Size: {size}")
  
    # Build params 
    params = build_search_params(
        query=query,
        highlight=highlight,
        sort=sort, 
        from_result=from_result,
        size=size,
        facets=facets
    )

    # Fetch data from API
    raw_data = await fetch_from_api(BASE_URL, params)
    if raw_data is None: 
        return None
    
    try:
        response = parse_api_response(raw_data, query, params)
    except Exception as e: 
        logger.error(f"Failed to parse API response: {e}")
        return None

    if save_response:
        await _save_response(response, query)

    log_search_results(response)

    return response


def build_search_params(query: str, highlight: bool =True, sort: str ="date desc",  from_result: int=1, size: int=DEFAULT_SIZE, facets: str="language person subject type_genre isPartOf") -> Dict[str, any]:

    """ Construct API request params: transform function arguments into the dictionary format expected by the EconBiz API """

    return {
        "q": query,
        "highlight": highlight,
        "sort": sort,
        "ff": 'source:"econstor"',
        "from": from_result,
        "size": size,
        "facets": facets
    }


async def fetch_from_api(BASE_URL: str, params: Dict[str, any], timeout: float = 30.0) -> Optional[Dict[str, any]]:

    """ Execute HTTP request and return raw JSON response """

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params = params, timeout = 30)
            response.raise_for_status()
            return response.json()
        
        except httpx.RequestError as e:
            logger.error(f"Error making API request: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occured: {e}")
            return None
        

def parse_api_response(raw_data: Dict[str, any], query: str, search_params: Dict[str, any]) -> EconBizResponse:

    """ Transfroms raw JSON into a validated EconBizResponse model """

    # Extract hits section 
    hits_data = raw_data.get('hits', {})

    # Parse individual papers
    papers = [Paper(**paper_data) for paper_data in hits_data.get('hits', [])]

    search_hits = SearchHits(total = hits_data.get('total', 0), hits = papers)

    return EconBizResponse(hits=search_hits, facets=raw_data.get('facets'), query=query, search_params=search_params)


def log_search_results(response: EconBizResponse) -> None:

    papers = response.get_papers()
    pdf_urls = response.get_pdf_urls()

    logger.info(f"Found {response.hits.total} total results")
    logger.info(f"Retrieved {len(papers)} papers")
    logger.info(f"Found {len(pdf_urls)} PDFs available:")
    
    for paper_id, url in pdf_urls:
        logger.debug(f"  PDF: {paper_id} → {url}")


async def _save_response(response: EconBizResponse, query: str)-> None:

    safe_query = query.replace(" ", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"response_{safe_query}_{timestamp}.json"
    filepath = Path("saved_responses")/filename

    # Await the async method from EconBizResponse 
    await response.save(filepath)
    logger.info(f"Response saved to: {filepath}")     