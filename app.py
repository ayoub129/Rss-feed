import os
from flask import Flask, jsonify
from dotenv import load_dotenv
import requests
import datetime

load_dotenv()

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('BASE_ID')
TABLE_NAME = os.getenv('TABLE_NAME')
VIEW_NAME = os.getenv('VIEW_NAME')
AIRTABLE_URL = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}?view={VIEW_NAME}'

# Initialize the Flask app
app = Flask(__name__)

def fetch_airtable_data():
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}'
    }
    response = requests.get(AIRTABLE_URL, headers=headers)
    return response.json().get('records', [])

def generate_json_feed(records):
    feed = {
        "channel": {
            "title": "Automadic RSS Feed",
            "link": "https://www.automadic.io",
            "description": "RSS Feed for Automadic",
            "language": "en-us",
            "copyright": "2025 Automadic. All rights reserved.",
            "lastBuildDate": datetime.datetime.utcnow().isoformat(),
            "image": {
                "url": "https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=380,fit=crop,q=95/mjE9loky0pCQ8rqG/93010e24-496f-4b76-a995-bc1994638bb6-dOq4BJ8Z2Qs",
                "title": "Automadic",
                "link": "https://www.automadic.io"
            },
            "items": []
        }
    }
    
    for record in records:
        fields = record.get('fields', {})
        title = fields.get('json_feed_title', 'No Title')
        image = fields.get('render_queue_image (from newsID_RSS_source)', 'No Image')
        link = fields.get('finalCreatomateURL', '#')
        newsID_RSS_source = fields.get('newsID_RSS_source', [])
        
        # Initialize arlink with a default value
        arlink = 'Link not found'

        # Airtable filter request
        headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}
        
        # Only make the request if newsID_RSS_source has items
        if newsID_RSS_source:
            params = {
                'filterByFormula': f"FIND('{newsID_RSS_source[0]}', {{newsID}}) > 0"
            }
            rss_source_url = f'https://api.airtable.com/v0/{BASE_ID}/RSS-Feed-PythonServer'

            try:
                response = requests.get(rss_source_url, headers=headers, params=params)
                if response.status_code == 200:
                    records = response.json().get('records', [])
                    if records:
                        arlink = records[0]['fields'].get('Link', 'Link not found')
            except requests.exceptions.RequestException as e:
                print(f"Error fetching Airtable Link data: {e}")

        created_at = fields.get('createdTime', datetime.datetime.utcnow().isoformat())

        feed["channel"]["items"].append({
            "title": title,
            "image": image,
            "link": link,
            "guid": record.get('id'),
            "pubDate": created_at,
            "article-url": arlink
        })
    
    return feed

@app.route('/delfi-xml')
def serve_json():
    records = fetch_airtable_data()
    json_feed = generate_json_feed(records)

    return jsonify(json_feed)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
