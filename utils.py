import requests
from pathlib import Path
from typing import List, Optional
from models import EconBizResponse

def load_saved_responses(filepath: Path) -> EconBizResponse:
    return EconBizResponse.load(filepath)


def list_saved_responses(directory: Path = Path("saved_responses")) -> List[Path]:

    if not directory.exists():
        return []

    saved_files = list(directory.glob("response_*.json"))
    return sorted(saved_files)


def download_pdf(url: str, filename: str, timeout: int = 30) -> bool:

    try: 
        response = requests.get(url, timeout=timeout)

        if response.status_code == 200:
            binary_data = response.content 

            with open(filename, "wb") as f: 
                f.write(binary_data)

            return True

        else: 
            print(f"Failed to download: HTTP {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print(f"Error downloading {url}: Timeout after {timeout}s")
        return False
    except requests.exceptions.ConnectionError:
        print(f"Error downloading {url}: Connection error")
        return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_pdfs_batch(pdf_urls: List[tuple], output_dir: Path = Path(".")) -> dict:
    output_dir.mkdir(parents = True, exist_ok = True)

    results = {'successful': [], 'failed': []}

    print(f"\nDownloading {len(pdf_urls)} PDFs...")

    for i, (paper_id, url) in enumerate(pdf_urls, 1):
        filename = output_dir / f"{paper_id}.pdf"

        success = download_pdf(url, str(filename))

        if success:
            print(f"Saved as {filename}")
            results['successful'].append(paper_id)
        else:
            print(f"Failed")
            results['failed'].append(paper_id)

    print(f"Download Summary:")
    print(f"Successful: {len(results['successful'])}")
    print(f"Failed: {len(results['failed'])}")

    return results


def format_paper_info(paper) -> str:

    lines = [f"Paper ID: {paper.id}"]

    if paper.title:
        lines.append(f"Title: {paper.title[0]}")

    if paper.creator_name:
        authors = ', '.join(paper.creator_name[:3])
        if len(paper.creator_name) > 3:
            authors += f" (and {len(paper.creator_name) - 3} more"
        lines.append(f"Authors: {authors}")

    if paper.date:
        lines.append(f"Date: {paper.date[0]}")

    pdf_url = paper.get_pdf_url()

    if pdf_url:
        lines.append(f"PDF: Available")
    else:
        lines.append(f"PDF: Not Available")

    if paper.subject:
        subjects = ', '>join(paper.subject[:3])
        if len(paper.subjects) > 3:
            subjects += "..."
        lines.append(f"Subjects: {subjects}")

    return '\n  '.join(lines)

