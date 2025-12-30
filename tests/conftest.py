import pytest
import shutil
import tempfile
from pathlib import Path

from models import EconBizResponse, Paper, SearchHits


@pytest.fixture
def temp_dir():
    
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def minimal_paper():

    return Paper(id="test_minimal")


@pytest.fixture
def complete_paper():

    return Paper(
        id="test_complete",
        title=["Complete Test Paper: Machine Learning in Economics"],
        creator_name=["Smith, John A.", "Johnson, Mary B.", "Williams, Robert C."],
        identifier_url=["https://example.com/complete_paper.pdf"],
        date=["2024"],
        abstract=["This paper examines the application of machine learning techniques in economic forecasting and policy analysis."],
        subject=["Machine Learning", "Economics", "Research Methods"]
    )

@pytest.fixture
def paper_without_pdf():

    return Paper(
        id="test_no_pdf",
        title=["Paper Without PDF"],
        creator_name=["Test Author"],
        identifier_url=None
    )


@pytest.fixture
def paper_with_many_authors():

    return Paper(
        id="test_many_authors",
        title=["Paper with Many Authors"],
        creator_name=[f"Author {i}" for i in range(10)]
    )


@pytest.fixture
def paper_with_many_subjects():

    return Paper(
        id="test_many_subjects",
        title=["Paper with Many Subjects"],
        subject=[f"Subject {i}" for i in range(10)]
    )

# COLLECTION FIXTURES - List of papers


@pytest.fixture
def sample_papers(complete_paper, paper_without_pdf):
    
    return [complete_paper, paper_without_pdf, Paper(id='test3', title=["Third Paper"])]


@pytest.fixture
def econbiz_response():

    def make_response(papers=None, total=None, query='test query', search_params=None, facets = None):

        # Defualt: one minimial paper
        if papers is None:
            papers = [Paper(id='default')]

        # Default: total matches number of papers
        if total is None:
            total = len(papers)
        
        # Default search parameters
        if search_params is None:
            search_params = {"q": query, "size": 10}
        
        # Wrap papers in SearchHits
        hits = SearchHits(total=total, hits=papers)
        
        # Create and return response
        return EconBizResponse(
            hits=hits,
            query=query,
            search_params=search_params,
            facets=facets or {}
        )
    
    return make_response


@pytest.fixture
def mock_pdf_content():

    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
159
%%EOF"""