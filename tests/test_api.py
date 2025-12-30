import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api import search
import httpx


class TestEconBizAPI:

    """ Tests entire flow from HTTP request to python objects """

    @pytest.fixture
    def mock_api_response(self):

        """ Realistic API response based on EconBiz documentation """

        return {
            "hits": {
                "total": 2,
                "hits": [
                    {
                        "id": "10419/12345",
                        "title": ["The Impact of Machine Learning on Economic Forecasting"],
                        "creator_name": ["Smith, John A.", "Johnson, Mary B.", "Williams, Robert C."],
                        "identifier_url": [
                            "https://www.econstor.eu/bitstream/10419/12345/1/paper.pdf",
                            "https://www.example.com/alternate.pdf"
                        ],
                        "date": ["2024"],
                        "abstract": ["This paper examines the growing role of machine learning..."],
                        "subject": ["Machine Learning", "Economic Forecasting", "Artificial Intelligence", "Econometrics"]
                    },
                    {
                        "id": "10419/67890",
                        "title": ["Neural Networks in Financial Markets"],
                        "creator_name": ["Davis, Emma"],
                        "identifier_url": ["https://www.econstor.eu/bitstream/10419/67890/1/finance.pdf"],
                        "date": ["2023"],
                        "abstract": ["We investigate neural network applications..."],
                        "subject": ["Finance", "Neural Networks"]
                    }
                ]
            },
            "facets": {
                "language": ["en", "de"],
                "subject": ["Machine Learning", "Finance", "Economics"],
                "type_genre": ["Article", "Working Paper"]
                }
            }
    

    @pytest.mark.asyncio
    async def test_valid_search_response(self, mock_api_response):

        """ 
        Test search function returns correct EconBizResponse object
        VALIDATES: 
            HTTP request
            JSON parsing
            Data transformation to python objects
            All fields accessible

        """
        # Mock HTTP response 
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = mock_api_response
        mock_http_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = await search(query="machine learning", size=10, save_response=False) 

        # Response object exists
        assert response is not None

        # Metadata is correct 
        assert response.query == "machine learning"
        assert response.hits.total == 2
        assert response.facets is not None

        # Papeprs correctly parsed
        papers = response.get_papers()
        assert len(papers) == 2

        # First paper has correct data 
        first_paper = papers[0]
        assert first_paper.id == "10419/12345"
        assert first_paper.title[0] == "The Impact of Machine Learning on Economic Forecasting"
        assert len(first_paper.creator_name) == 3
        assert first_paper.creator_name[0] == "Smith, John A."

        # PDF URL extraction
        pdf_url = first_paper.get_pdf_url()
        assert pdf_url == "https://www.econstor.eu/bitstream/10419/12345/1/paper.pdf"

        # Second paper parsed 
        second_paper = papers[1]
        assert second_paper.id == "10419/67890"
        assert len(second_paper.creator_name) == 1

        all_pdf_urls = response.get_pdf_urls()
        assert len(all_pdf_urls) == 2
        assert all_pdf_urls[0] == ("10419/12345", "https://www.econstor.eu/bitstream/10419/12345/1/paper.pdf")
        assert all_pdf_urls[1] == ("10419/67890", "https://www.econstor.eu/bitstream/10419/67890/1/finance.pdf")

        # Facets preserved 
        assert "language" in response.facets
        assert "en" in response.facets["language"]


    @pytest.mark.asyncio
    async def test_correct_parameters(self, mock_api_response):

        """ Validates parameters are constructed correctly in HTTP request """

        mock_http_response = MagicMock()
        mock_http_response.json.return_value = mock_api_response
        mock_http_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await search(query="economics", size=25, from_result=5, sort="relevance desc", save_response=False)

            # Verify correct parameters passed to HTTP request
            call_args = mock_client.get.call_args

            assert call_args[0][0] == "https://api.econbiz.de/v1/search"
            params = call_args[1]['params']
            assert params["q"] == "economics"
            assert params["size"] == 25
            assert params["from"] == 5
            assert params["sort"] == "relevance desc"
            assert params["ff"] == 'source:"econstor"'


    @pytest.mark.asyncio
    async def test_papers_without_pdfs(self):

        """ Validates papers without PDF URLs are handled correctly """

        response_missing_pdfs = {
        "hits": {
            "total": 3,
            "hits": [
                {
                "id": "paper1",
                    "title": ["Paper with PDF"],
                    "identifier_url": ["https://example.com/1.pdf"]
                },
                {
                    "id": "paper2",
                    "title": ["Paper without PDF"],
                    "identifier_url": None  # No PDF
                },
                {
                    "id": "paper3",
                    "title": ["Another paper with PDF"],
                    "identifier_url": ["https://example.com/3.pdf"]
                }
            ]
        }
    }   
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = response_missing_pdfs
        mock_http_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class: 
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = await search(query='test', save_response=False)

        assert len(response.get_papers()) == 3
        pdf_urls = response.get_pdf_urls()
        assert len(pdf_urls) == 2  # Only 2 papers have PDFs
        assert pdf_urls[0] == ("paper1", "https://example.com/1.pdf")
        assert pdf_urls[1] == ("paper3", "https://example.com/3.pdf")


    @pytest.mark.asyncio
    async def test_empty_response(self):

        """ Validates handling of empty search results returned by API """

        empty_response = {
            "hits": {
                "total": 0,
                "hits": []
            },
            "facets": {}
        }

        mock_http_response = MagicMock()
        mock_http_response.json.return_value = empty_response
        mock_http_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = await search(query="nonexistent query", save_response=False)

        assert response is not None
        assert response.hits.total == 0
        assert len(response.get_papers()) == 0
        assert response.get_pdf_urls() == []

class TestAPIErrorHandling:

    """ Tests error handling in API requests"""

    @pytest.mark.asyncio
    async def test_network_timeout(self):

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = await search(query="test", save_response=False)

            assert response is None

    @pytest.mark.asyncio
    async def test_404_error(self):

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=mock_response)

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = await search(query="test", save_response=False)

        assert response is None

    @pytest.mark.asyncio
    async def test_malformed_json(self):

        """ Validates handling of parsing erros from invalid JSON structure"""

        invalid_response = {"wrong_field": "unexpected structure"}

        mock_http_response = MagicMock()
        mock_http_response.json.return_value = invalid_response
        mock_http_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_http_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = await search(query='test', save_response=False)

        assert response is None
    
    


            