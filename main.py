import requests
import json

BASE_URL = "https://api.econbiz.de/v1/search"
DEFAULT_SIZE = 10


def main():
    query = input("Enter search term: ")
    print(f"Searching for: {query}")
  

    params = { 
        "q": query,
        "ff": 'source:"econstor"', 
        "from": 1,
        "size": DEFAULT_SIZE }

    print("Making API request")
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        print("success, here's requested data")
        print(json.dumps(data))

    else: print(f"Error: {response.status_code}")


if __name__ == "__main__":
    main()
