import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from utils import download_pdf, download_pdfs_batch
import httpx


class TestPDFDownload:
     
    @pytest.mark.asyncio 
    async def test_pdf_download_success(self, temp_dir, mock_pdf_content):

        """ Validates file is created and function returns True on success"""
        
        filename = temp_dir / "test_paper.pdf"

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.content = mock_pdf_content
        mock_response.raise_for_status = MagicMock()

        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_response
        mock_stream.__aexit__.return_value = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client    

            result = await download_pdf("https://example.com/test.pdf", str(filename))

            assert result is True
            assert filename.exists()

            content = filename.read_bytes()
            assert content == mock_pdf_content


    @pytest.mark.asyncio
    async def test_pdf_download_timeout(self, temp_dir):

        """ Validates function returns False on timeout """

        filename = temp_dir / "test_paper.pdf"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await download_pdf("https://example.com/test.pdf", str(filename), timeout=1)

        assert result is False
        assert not filename.exists()

    @pytest.mark.asyncio
    async def test_download_pdfs_batch(self, temp_dir):

        """ Validates batch download of PDFs with mixed success """
        
        pdf_urls = [
            ("paper1", "https://example.com/paper1.pdf"), 
            ("paper2", "https://example.com/paper2.pdf"), 
            ("paper3", "https://example.com/paper3.pdf")
            ]
        
        # Mock: paper1 and paper3 succeed, paper 2 fails 
        async def mock_download(url, filename):
            if "paper2" in url:
                return False
            return True
        
        with patch("utils.download_pdf", side_effect=mock_download):
            results = await download_pdfs_batch(pdf_urls, output_dir=temp_dir)

        assert len(results['successful']) == 2
        assert len(results['failed']) == 1
        assert "paper2" in results['failed']
        assert "paper1" and "paper3" in results['successful']


    @pytest.mark.asyncio
    async def test_ouputdir_created(self, temp_dir):

        """ Test that output directory is created if does not exist"""

        output_dir = temp_dir / "nonexistent" / "downloads"
        pdf_urls = [("test", "https://example.com/test.pdf")]

        async def mock_download(url, filename):
            return True
        
        with patch('utils.download_pdf', side_effect=mock_download):
            await download_pdfs_batch(pdf_urls, output_dir=output_dir)

        assert output_dir.exists()


