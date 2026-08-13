import requests
import cloudscraper

def test_api(url):
    print(f"Testing URL: {url}")
    
    # 1. Test using requests
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers)
        print(f"Requests status: {resp.status_code}")
    except Exception as e:
        print(f"Requests error: {e}")

    # 2. Test using cloudscraper
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        resp = scraper.get(url, headers=headers)
        print(f"Cloudscraper status: {resp.status_code}")
    except Exception as e:
        print(f"Cloudscraper error: {e}")

test_api("https://api.sofascore.com/api/v1/sport/football/events/live")
test_api("https://www.sofascore.com/api/v1/sport/football/events/live")
test_api("https://api.sofascore.app/api/v1/sport/football/events/live")
