import os
import requests
import logging
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))

SA_API_KEY = os.getenv('SA_API_KEY')

def getAllSeries():
    url_base = "https://api.sermonaudio.com/v2/node/broadcasters/calvaryfaytn/series"
    page = 1
    titles = []
    while True:
        # Make API request for the current page
        url = f"{url_base}?sort_by=last_updated&filterBy=all&page={page}&pageSize=5"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Extract titles from the 'results' array and add to the main titles list
            titles.extend([series['title'] for series in data['results']])
            
            # Check if there are more pages
            if 'next' in data and data['next']:
                page += 1
            else:
                break  # No more pages, exit the loop
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            break  # Stop if there's an error

    return titles

def createSermon():
    pass


def uploadSermon(filePath, sermonId, uploadType="original"):
    url = "https://api.sermonaudio.com/v2/media"
    
    headers = {
        "accept": "application/json",
        "X-Site-Auth-Username": SA_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "uploadType": uploadType,
        "sermonID": sermonId
    }

    try:
        with open(filePath, "rb") as file:
            files = {"file": file}
            response = requests.post(url, headers=headers, data=data, files=files)

            if response.status_code == 200:
                successData = response.json
                return successData
                print("File uploaded successfully.")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    all_titles = getAllSeries()
    print(all_titles)
