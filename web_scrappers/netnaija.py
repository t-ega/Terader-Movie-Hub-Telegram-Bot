import aiohttp
from bs4 import BeautifulSoup


async def netnaija_web_scrapper(title) -> list:
    title = title.replace('-', ' ')
    title = title.replace(' ', '+')
    title = title.replace(':', '')

    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://www.thenetnaija.net/search?t={title}&folder=videos') as req:
            # Read the response content asynchronously
            response_text = await req.text()

    soup = BeautifulSoup(response_text, 'lxml')
    soup = soup.find('div', id='content')
    soup = soup.find('div', class_='search-results')
    soup = soup.find_all('a')

    if len(soup) == 1:
        return [{'text':soup[0].text, 'url':soup[0].get('href')}]

    title = title.replace('+', '-')
    title = title.lower()

    links = [{"text": link.text, "url": link.get('href')} for link in soup if title in link.get('href')]
    return links
