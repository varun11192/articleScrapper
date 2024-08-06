from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import json

app = FastAPI()

class URLModel(BaseModel):
    url: str

def extract_article_content(url: str):
    try:
        response = requests.get(url)

        if response.status_code != 200:
            raise HTTPException(status_code=500,
                                detail=f"Failed to retrieve the webpage. Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting title
        title_tag = soup.find('meta', property='og:title')
        title = title_tag['content'] if title_tag else 'No title found'

        # Extracting description
        description_tag = soup.find('meta', property='og:description')
        description = description_tag['content'] if description_tag else 'No description found'

        # Extracting body
        entry_div = soup.find('div', class_='entry')
        body = ''

        if entry_div:
            paragraphs = entry_div.find_all('p')
            body = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

        # Extracting modified date
        modified_date_tag = soup.find('meta', property='article:modified_time')
        modified_date = modified_date_tag['content'] if modified_date_tag else 'No modified date found'

        # Extracting published date
        published_date_tag = soup.find('meta', property='article:published_time')
        if not published_date_tag:
            # If the meta tag for published date is not found, look in the script tags for JSON-LD
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                json_data = json.loads(script.string)
                if '@type' in json_data and json_data['@type'] == 'BlogPosting':
                    published_date = json_data.get('datePublished', 'No published date found')
                    break
            else:
                published_date = 'No published date found'
        else:
            published_date = published_date_tag['content']

        return {
            'title': title,
            'description': description,
            'body': body,
            'modified_date': modified_date,
            'published_date': published_date
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/extract-content/")
def extract_content(url_model: URLModel):
    return extract_article_content(url_model.url)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Link Scraper API. Use the /extract-content/ endpoint to scrape article content."}
