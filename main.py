import requests
import json
from pydantic import BaseModel, Field 
from typing import Optional, List, Tuple
from datetime import datetime
from pathlib import Path 


BASE_URL = "https://api.econbiz.de/v1/search"
DEFAULT_SIZE = 10


class Paper(BaseModel):  # individual papers
    id: str 
    title: Optional[List[str]] = None 
    creator_name: Optional[List[str]] = None
    identifier_url: Optional[List[str]] = None
    date: Optional[List[str]] = None
    abstract: Optional[List[str]] = None
    subject: Optional[List[str]] = None


    def get_pdf_url(self) -> Optional[str]: 
        if self.identifier_url and len(self.identifier_url)>0: #extract first PDF URL
            return self.identifier_url[0]

        return None




class SearchHits(BaseModel): # search results 
    total: int 
    hits: List[Paper]




class EconBizResponse(BaseModel): # complete API response
    hits: SearchHits
    facets: Optional[dict] = None
    query: str = ""
    search_params: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    def get_papers(self) -> List[Paper]:
        return self.hits.hits


    def get_pdf_urls(self) -> List[Tuple[str, str]]:
        results = []

        for paper in self.get_papers():
            pdf_url = paper.get_pdf_url()

            if pdf_url:
                results.append(paper.id, pdf_url)
        return results

    
    def save(self, filepath: Path) -> None:
        filepath.parent.mkdir(parents = True, exist_ok = True)
        filepath.write_text(self.model_dump_json(indent=2))


    @classmethod
    def load(cls, filepath: Path) -> 'EconBizResponse':
        return cls.model_validate_json(filepath.read_text())




def main(query, highlight=True, sort="date desc",  from_result=1, size=DEFAULT_SIZE, facets="language person subject type_genre isPartOf", save_response=True):
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
    
        try: #conversion to pydantic model 
            econbiz_response = EconBizResponse(hits=SearchHits(total=raw_data['hits']['total'],
            hits=[Paper(**paper) for paper in raw_data['hits']['hits']]),
            facets=raw_data.get('facets'),
            query=query,
            search_params=params
            )

            if save_response: #conditional save - user dependent 
                safe_query = query.replace(" ", "_").replace("/", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = Path("saved_responses") / f"response_{safe_query}_{timestamp}.json"
                econbiz_response.save(filepath)
                print(f"Response saved to: {filepath}") 

            papers = econbiz_response.get_pdf_urls()
            pdf_urls = econbiz_response.get_papers()

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


def load_saved_responses(filepath: Path) -> EconBizResponse:
    return EconBizResponse.load(filepath)


def download_pdfs(url, filename):

    try: 
        response = requests.get(url)

        if response.status_code == 200:
            binary_data = response.content 

            with open(filename, "wb") as f: 
                f.write(binary_data)

            return True

        else: 
            print(f"Failed to download: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False
    


if __name__ == "__main__":

    # first run - API call and save responses 
    print("What would you like to do?")
    print("1. Search for a paper") # API call
    print("2. Load a saved response") # No API call 

    choice = input("Enter choice 1 or 2: ").strip()

    # CHOICE 1: SEARCH (API CALL)

    if choice == "1":
        query = input("Enter search query: ").strip()

        size_input = input("Number of papers (default 10): ").strip()
        size = int(size_input) if size_input else 10

        save_input = input("Save responses for later? (y/n, default y): ").strip().lower()
        save = save_input != 'n'

        response = main(query=query, size=size, save_responses=save)

        if response:
            papers = response.get_papers()
            print(f"\n Successfully retrieved {len(papers)} papers")
            print(f" Total results available: {response.hits.total}")

            print("\nPapers found:")
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. ID: {paper.id}")
                if paper.title:
                    print(f"   Title: {paper.title[0]}")
                if paper.creator_name:
                    print(f"   Authors: {', '.join(paper.creator_name)}")
                print(f"   PDF: {paper.get_pdf_url() or 'Not available'}")

            pdf_urls = response.get_pdf_urls()
            if pdf_urls:
                download = input(f"\nDownload {len(pdf_urls)} PDFs? (y/n): ").strip().lower()
                if download == 'y':
                    for paper_id, url in pdf_urls:
                        filename = f"{paper_id}.pdf"
                        print(f"Downloading {filename}...")
                        download_pdfs(url, filename) 
                        print(f"Downloaded {filename}")
        else:
            print("Search failed. Check your internet connection.")

    # CHOICE 2: Load Saved Response

    if choice == '2':
        saved_dir = Path("saved_responses")

        if not saved_dir.exists() or not list(saved_dir.glob("response_*.json")):
            print("\nNo saved responses found")
        else:
            saved_files = sorted(list(saved_dir.glob("response_*.json")))

            print("\nSaved searches:")
            for i, file in enumerate(saved_files, 1):
                r = EconBizResponse.load(file)
                print(f"[{i}] {r.query} - {r.timestamp}")

            selection = input("\nSelect (or Enter for latest): ").strip()
            index = int(choice) - 1 if choice else -1

            loaded = EconBizResponse.load(saved_files[index])

            print(f"\nLoaded '{loaded.query}'")
            print(f"Papers: {len(loaded.get_papers())}")
        
            for i, paper in enumerate(loaded.get_papers(), 1):
                print(f"\n[{i}] {paper.id}")
                if paper.title:
                    print(f"{paper.title[0]}")

            

   