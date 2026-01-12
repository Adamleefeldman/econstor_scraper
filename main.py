import asyncio
import logging
from pathlib import Path 
from models import EconBizResponse
from api import search
from utils import (load_saved_responses, list_saved_responses, download_pdfs_batch, format_paper_info)


logging.basicConfig(level=logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s', handlers = [
    logging.FileHandler("econstor_scraper.log"),
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)


def display_search_results(response: EconBizResponse) -> None: 

    """Displays search results in correctly formatted way"""

    papers = response.get_papers()

    logger.info(f"Successfully retrieved {len(papers)} papers")
    logger.info(f"Total results available: {response.hits.total}")

    for i, paper in enumerate(papers, 1):
        logger.info(f"[{i}] {format_paper_info(paper)}")


async def offer_pdf_download(pdf_urls) -> None:

    """ Facilitates PDF download process """

    if not pdf_urls:
        return
    
    download = input(f"\nDownload {len(pdf_urls)} PDF(s)? (y/n): ").strip().lower()

    if download == 'y':
        results = await download_pdfs_batch(pdf_urls)

        # Display results 
        logger.info("Download results:")
        logger.info(f"  Successful downloads: {len(results['successful'])}")
        logger.info(f"  Failed downloads: {len(results['failed'])}")


async def handle_search_mode() -> None:

    """Handles online search mode, makes API call to EconBiz"""

    query = input("\nEnter search query: ").strip()

    if not query: 
        logger.info("Query cannot be empty ")
        return 

    size_input = input("Number of papers (default 10): ").strip()
    size = int(size_input) if size_input else 10

    save_input = input("Save response? (y/n, default y): ").strip().lower()
    save = save_input != 'n'

    response = await search(query=query, size=size, save_response=save)

    if response: 
        display_search_results(response)

        pdf_urls = response.get_pdf_urls()
        await offer_pdf_download(pdf_urls)

    else:
        logger.error("Search failed")


async def handle_load_mode() -> None:

    """ Facilitates offline loading mode - loads saved responses from disk """

    saved_dir = Path("saved_responses")
    saved_files = list_saved_responses(saved_dir) # Synchronous function 

    if not saved_files:
        logger.info("No saved responses")
        return 

    logger.info(f"Found {len(saved_files)} saved files:")

    # Load metadata for each saved file
    for i, filepath in enumerate(saved_files, 1):
        try:
            r = await load_saved_responses(filepath)
            if r:
                logger.info(f"[{i}] {r.query} - {r.timestamp}")
            else:
                logger.info(f"[{i}] Error loading: {filepath.name}")

        except Exception as e:
            logger.error(f"[{i}] Error loading: {filepath.name} - {e}")

    selection = input("\nSelect (or Enter for latest): ").strip()

    try:
        if selection == "":
            index = -1  
        else:
            index = int(selection) - 1

        selected_file = saved_files[index]

        loaded = await load_saved_responses(selected_file)

        if not loaded:
            logger.info("Failed to load selected response")
            return 

        logger.info(f"Loaded successfully!")
        logger.info(f"   Query: '{loaded.query}'")
        logger.info(f"   Saved: {loaded.timestamp}")
        logger.info(f"   Papers: {len(loaded.get_papers())}")


        for i, paper in enumerate(loaded.get_papers(), 1):
            logger.info(f"[{i}] {format_paper_info(paper)}")

        #PDF download
        pdf_urls = loaded.get_pdf_urls()
        await offer_pdf_download(pdf_urls)


    except ValueError:
        logger.info("Invalid input. Please enter a number.")
    except Exception as e:
        logger.error(f"Error: {e}")


async def main() -> None:

    logger.info("-" * 70)
    logger.info("ECONBIZ RESEARCH PAPER SEARCH TOOL")
    logger.info("-" * 70)

    while True:
        
        # Show menu
        logger.info("What would you like to do?")
        logger.info("[1] Search EconBiz (makes API call)")
        logger.info("[2] Load saved response (no API call, works offline)")
    
        choice = input("\nEnter 1 or 2 (or 'q' to quit): ").strip()
        
        # Route to appropriate handler
        if choice == "1":
            await handle_search_mode()
        elif choice == "2":
            await handle_load_mode()
        elif choice == "q":
            logger.info("Thank you for using our tool. Goodbye")
            break
        else:
            logger.info("Invalid choice. Please enter 1, 2 or q.")

    logger.info("Program terminated successfully")

if __name__ == "__main__":
    asyncio.run(main())




        


        