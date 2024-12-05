EventBrite Scraper
=====================

A Python script to scrape event data from EventBrite.

## Overview
This script uses the requests and BeautifulSoup libraries to scrape event data from EventBrite. It fetches event URLs from a given search page, extracts event information from each event page, and saves the data to a JSON file.

## Requirements
* Python 3.8+

## Usage
1. Clone the repository: `git clone https://github.com/natnaelab/eventbrite-scraper.git`
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install the requirements: `pip install -r requirements.txt`
5. Run the script: `python main.py`
6. Enter the EventBrite search page URL when prompted
7. The script will fetch event data and save it to a JSON file named `event_datas/event_data_<random_string>.json`

## Notes
The script may break if EventBrite changes its website structure or adds anti-scraping measures.
