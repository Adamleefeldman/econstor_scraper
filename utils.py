import httpx
import aiofiles
import asyncio 
from pathlib import Path
from typing import List, Optional
from models import EconBizResponse
import logging 

logger = logging.getLogger(__name__)

async def load_saved_responses(filepath: Path) -> Optional[EconBizResponse]:
    
    try:
        return await EconBizResponse.load(filepath)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return None
    except Exception as e: 
        logger.error(f"Error loading response from {filepath}: {e}")
        return None 

def list_saved_responses(directory: Path = Path("saved_responses")) -> List[Path]:

    if not directory.exists():
        return []

    saved_files = list(directory.glob("response_*.json"))
    return sorted(saved_files)


async def download_pdf(url: str, filename: str, timeout: int = 30) -> bool:

    try: 
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, stream=True)
            response.raise_for_status()

            # Write file asynchronously
            async with aiofiles.open(filename, "wb") as f:
                await f.write(response.content)
            return True

    except httpx.TimeoutException:
        logger.error(f"Error downloading {url}: Timeout after {timeout}s")
        return False
    except httpx.ConnectError:
        logger.error(f"Error downloading {url}: Connection error")
        return False
    except httpx.HTTPStatusError as e:
        logger.error(f"Error downloading {url}: HTTP {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False

async def download_pdfs_batch(pdf_urls: List[tuple], output_dir: Path = Path(".")) -> dict:
    output_dir.mkdir(parents = True, exist_ok = True)

    """
        Download multiple PDFs concurrently
        
        Args:
            pdf_urls: List of tuples containing (paper_id, pdf_url)
            output_dir: Directory to save downloaded PDFs
            
        Returns: 
                Dict with 'successful' 'failed' paper IDs
    """

    results = {'successful': [], 'failed': []}

    logger.info(f"Downloading {len(pdf_urls)} PDFs...")
    
    tasks = []
    for paper_id, url in pdf_urls:
        filename = output_dir / f"{paper_id}.pdf"
        task = download_pdf(url, str(filename)) # Create the async download task 
        tasks.append((paper_id, url, filename, task))

    download_results = await asyncio.gather(*[task for _, _, _, task in tasks], return_exceptions=True)

    for (paper_id, url, filename, _), success in zip(tasks, download_results):
        if isinstance(success, Exception):
            logger.warning(f"Failed to download {paper_id}: {success}")
            results['failed'].append(paper_id)
        elif success:
            logger.debug(f"Saved {paper_id} as {filename}")
            results['successful'].append(paper_id)
        else:
            logger.warning(f"Failed to download {paper_id}")
            results['failed'].append(paper_id)

    logger.info(f"Download Summary:")
    logger.info(f"Successful: {len(results['successful'])}")
    logger.info(f"Failed: {len(results['failed'])}")

    return results


def format_paper_info(paper) -> str:

    lines = [f"Paper ID: {paper.id}"]

    if paper.title:
        lines.append(f"Title: {paper.title[0]}")

    if paper.creator_name:
        authors = ', '.join(paper.creator_name[:3])
        if len(paper.creator_name) > 3:
            authors += f" (and {len(paper.creator_name) - 3} more)"
        lines.append(f"Authors: {authors}")

    if paper.date:
        lines.append(f"Date: {paper.date[0]}")

    pdf_url = paper.get_pdf_url()

    if pdf_url:
        lines.append(f"PDF: Available")
    else:
        lines.append(f"PDF: Not Available")

    if paper.subject:
        subjects = ', '.join(paper.subject[:3])
        if len(paper.subject) > 3:
            subjects += "..."
        lines.append(f"Subjects: {subjects}")

    return '\n  '.join(lines)

