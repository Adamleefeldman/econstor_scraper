import requests
import json

BASE_URL = "https://api.econbiz.de/v1/search"
DEFAULT_SIZE = 10


def main(query, highlight=True, sort="date desc",  from_result=1, size=DEFAULT_SIZE, facets="language person subject type_genre isPartOf" ):
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
        data = response.json()
        papers = data['hits']['hits']

        pdf_urls = extract_pdf_urls(papers)

        print("success, here's requested data")

        print(f"\nFound {len(pdf_urls)} PDFs:")
        for paper_id, url in pdf_urls:
            print(f"  {paper_id}: {url}")
        #print(json.dumps(data, indent=2))

    else: print(f"Error: {response.status_code}")


def extract_pdf_urls(papers):
    results = []

    for paper in papers:

        url_list = paper.get('identifier_url', [])

        if len(url_list) > 0:  #check if list has URLS and add 1st url to results as tuple 
            pdf_url = url_list[0] 
            paper_id = paper.get('id')
            results.append((paper_id,  pdf_url))

    return results 


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
     main("inflation", sort="date asc", size=1)  # Just 1 paper

    # Test download
     test_url = "https://www.econstor.eu/bitstream/10419/286074/1/9783428574988.pdf"
     success = download_pdfs(test_url, "test.pdf")

    
     if success:
        print("✓ PDF downloaded! Check your folder for test.pdf")
