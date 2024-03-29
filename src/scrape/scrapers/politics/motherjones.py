from uuid import uuid4

from scrape import html_scraper


@html_scraper('https://www.motherjones.com')
def scrape_motherjones(soup):
    return [dict(id=uuid4(), title=t.text.strip())
            for t in soup.find_all('h3', {'class': 'hed'})]


SCRAPERS = [scrape_motherjones]
