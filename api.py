import requests
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import Paper, EconBizResponse, SearchHits


BASE_URL = "https://api.econbiz.de/v1/search"
DEFAULT_SIZE = 10

def search(query, highlight=True, sort="date desc",  from_result=1, size=DEFAULT_SIZE, facets="language person subject type_genre isPartOf", save_response=True) -> Optional[EconBizResponse]:
    print(f"Searching for: {query}")
    print(f"From position: {from_result}, Size: {size}")
  
    params = {
        "q": query,
        "highlight": highlight,
        "sort": sort,
        "ff": 'source:"econstor"', 
        "from": from_result,
        "size": size,
        "facets": facets }

    print("Making API request")
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        raw_data = response.json()
    
        try: #conversion raw json to pydantic model 
            econbiz_response = EconBizResponse(hits=SearchHits(total=raw_data['hits']['total'],
            hits=[Paper(**paper) for paper in raw_data['hits']['hits']]),
            facets=raw_data.get('facets'),
            query=query,
            search_params=params
            )

            if save_response: #conditional save - user dependent 
                _save_response(econbiz_response, query)

            papers = econbiz_response.get_papers()
            pdf_urls = econbiz_response.get_pdf_urls()

            print(f"Found {econbiz_response.hits.total} total results")
            print(f"Retrieved {len(papers)} papers")
            print(f"Found {len(pdf_urls)} PDFs:")

            for paper_id, url in pdf_urls:
                print(f" {paper_id}, {url}")

            return econbiz_response

        except Exception as e:
            print(f"Error: {e}")
            return None 

    else: print(f"Error: {response.status_code}")


    def _save_response(response: EconBizResponse, query: str)-> None:

        safe_query = query.replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"response_{safe_query}_{timestamp}.json"
        filepath = Path("saved_responses")/filename

        response.save(filepath)
        print(f"Response saved to: {filepath}")     