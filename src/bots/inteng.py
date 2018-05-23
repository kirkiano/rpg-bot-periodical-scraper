from uuid import uuid4

from bs4 import BeautifulSoup

from web import get_web_page


async def scrape_inteng():
    r = await get_web_page('https://interestingengineering.com')
    soup = BeautifulSoup(r, 'html.parser')
    tags = []
    for cls, get_title in (
            ('main-post-title', lambda t: t['title']),
            ('main-video-title', lambda t: t.text),
            ('featured-image', lambda t: t['title'])):
        tags += [dict(id=uuid4(), title=get_title(t))
                 for t in soup.find_all('a', {'class': cls})]
    return tags
