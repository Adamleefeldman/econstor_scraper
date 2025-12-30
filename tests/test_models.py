import pytest
from datetime import datetime 
from models import EconBizResponse, SearchHits, Paper

class TestPaperModel:

    def test_paper_only_id(self, minimal_paper): # Miniumal valid paper
        paper = Paper(id = "123")

        assert minimal_paper.id == "test_minimal"
        assert minimal_paper.title is None
        assert minimal_paper.creator_name is None


    def test_paper_all_fields(self, complete_paper): # Full paper data 

        assert complete_paper.id == "test_complete"
        assert complete_paper.title == ["Complete Test Paper: Machine Learning in Economics"]
        assert len(complete_paper.creator_name) == 3
        assert complete_paper.identifier_url[0] == "https://example.com/complete_paper.pdf"

    
    def test_paper_get_pdf_url_extracts_first(self): # 1st PDF URL extraction 

        paper = Paper(id = "test", identifier_url=["https://example.com/paper.pdf", "https://example.com/other.pdf"])
        assert paper.get_pdf_url() == "https://example.com/paper.pdf"


    def test_paper_get_pdf_no_url(self, paper_without_pdf): # Paper has no URL 

        assert paper_without_pdf.get_pdf_url() is None


    def test_paper_get_pdf_url_empty_list(self): # Paper has empty identifier_url list

        paper = Paper(id = "test", identifier_url=[])
        assert paper.get_pdf_url() is None



class TestSearchHitsModel:

    """ Tests SearchHits which wraps papers with metadata """

    def test_search_hits_total(self, sample_papers):
    
        hits = SearchHits(total=100, hits=sample_papers[:2])
        assert hits.total == 100
        assert len(hits.hits) == 2 
        assert hits.hits[0].id == "test_complete"


    def test_search_hits_empty(self):

        hits = SearchHits(total = 0, hits = [])
        assert hits.total == 0
        assert hits.hits == []



class TestEconBizResponseModel:

    """ Main data returned by the api.search() """

    def test_response_structure(self, econbiz_response): 
        # Complete API response, validates EconBizResponse correctly wraps data

        response = econbiz_response(
            papers=[Paper(id="1", title=["Test"])],
            total=1,
            query="test query",
            search_params={"q": "test", "size": 10},
            facets={"language": ["en"]}
        )
        
        assert response.hits.total == 1
        assert response.query == "test query"
        assert response.search_params["size"] == 10
        assert response.facets["language"] == ["en"]
        assert isinstance(response.timestamp,  datetime)

    
    def test_get_papers(self, sample_papers, econbiz_response):
        
        response = econbiz_response(papers=sample_papers, total=3)

        result = response.get_papers()

        assert len(result) == 3
        assert all(isinstance(p, Paper) for p in result)

    def test_get_pdf_urls(self, complete_paper, paper_without_pdf):
        # get_pdf_urls returns only papers with valid PDF URLs

        papers = [
            complete_paper, 
            paper_without_pdf,
            Paper(id="p3", identifier_url=["https://example.com/3.pdf"]),  # Has PDF
            Paper(id="p4", identifier_url=[])  # Empty list 
            ]

        hits = SearchHits(total = 4, hits = papers)
        response = EconBizResponse(hits = hits, query="test")
        pdf_urls = response.get_pdf_urls()

        assert pdf_urls[0] == ("test_complete", "https://example.com/complete_paper.pdf")
        assert pdf_urls[1] == ("p3", "https://example.com/3.pdf")


    def test_returns_tuples(self, complete_paper, econbiz_response):
        # get_pdf_urls returns list of tuples (paper_id, pdf_url)

        response = econbiz_response(papers=[complete_paper])
        pdf_urls = response.get_pdf_urls()

        paper_id, url = pdf_urls[0]
        assert isinstance(paper_id, str)
        assert isinstance(url, str)
        assert paper_id == "test_complete" 




        




