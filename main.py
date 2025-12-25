import asyncio
from pathlib import Path 
from models import EconBizResponse
from api import search
from utils import (load_saved_responses, list_saved_responses, download_pdfs_batch, format_paper_info)


def display_search_results(response: EconBizResponse) -> None: 
    papers = response.get_papers()

    print(f"Successfully retrieved {len(papers)} papers")
    print(f"Total results available: {response.hits.total}")

    for i, paper in enumerate(papers, 1):
        print(f"\n[{i}] {format_paper_info(paper)}")


async def handle_search_mode() -> None:
    query = input("\nEnter search query: ").strip()

    if not query: 
        print(f"Query cannot be empty ")
        return 

    size_input = input("Number of papers (default 10): ").strip()
    size = int(size_input) if size_input else 10

    save_input = input("Save response? (y/n, default y): ").strip().lower()
    save = save_input != 'n'

    response = await search(query=query, size=size, save_response=save)

    if response: 
        display_search_results(response)

        pdf_urls = response.get_pdf_urls()
        if pdf_urls:
            download = input(f"\nDownload {len(pdf_urls)} PDFs? (y/n): ").strip().lower()

            if download == 'y': 
                results = await download_pdfs_batch(pdf_urls)

                # Display results 
                print("\nDownload results:")
                print(f"  Successful downloads: {len(results['successful'])}")
                print(f"  Failed downloads: {len(results['failed'])}")

    else:
        print("\nSearch failed")


async def handle_load_mode() -> None:
    saved_dir = Path("saved_responses")
    saved_files = list_saved_responses(saved_dir) # Synchronous function 

    if not saved_files:
        print("\nNo saved responses")
        return 

    print(f"\nFound {len(saved_files)} saved files:")

    # Load metadata for each saved file
    for i, filepath in enumerate(saved_files, 1):
        try:
            r = await load_saved_responses(filepath)
            if r:
                print(f"[{i}] {r.query} - {r.timestamp}")
            else:
                print(f"[{i}] Error loading: {filepath.name}")

        except Exception as e:
            print(f"[{i}] Error loading: {filepath.name} - {e}")

    selection = input("\nSelect (or Enter for latest): ").strip()

    try:
        if selection == "":
            index = -1  
        else:
            index = int(selection) - 1

        selected_file = saved_files[index]

        loaded = await load_saved_responses(selected_file)

        if not loaded:
            print("Failed to load selected response")
            return 

        print(f"\nLoaded successfully!")
        print(f"   Query: '{loaded.query}'")
        print(f"   Saved: {loaded.timestamp}")
        print(f"   Papers: {len(loaded.get_papers())}")


        for i, paper in enumerate(loaded.get_papers(), 1):
            print(f"\n[{i}] {format_paper_info(paper)}")

        #PDF download
        pdf_urls = loaded.get_pdf_urls()
        if pdf_urls:
            download = input(f"\nDownload {len(pdf_urls)} PDF(s)? (y/n): ").strip().lower()

            if download == 'y':
                results = await download_pdfs_batch(pdf_urls)

                # Display results 
                print("\nDownload results:")
                print(f"  Successful downloads: {len(results['successful'])}")
                print(f"  Failed downloads: {len(results['failed'])}")


    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"Error: {e}")


async def main() -> None:

    print("\n" + "=" * 70)
    print("ECONBIZ RESEARCH PAPER SEARCH TOOL")
    print("=" * 70)
    
    # Show menu
    print("\nWhat would you like to do?")
    print("[1] Search EconBiz (makes API call)")
    print("[2] Load saved response (no API call, works offline)")
    
    choice = input("\nEnter 1 or 2: ").strip()
    
    # Route to appropriate handler
    if choice == "1":
        await handle_search_mode()
    elif choice == "2":
        await handle_load_mode()
    else:
        print("\nInvalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    asyncio.run(main())




        


        