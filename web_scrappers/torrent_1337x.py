import ssl
import aiohttp
from bs4 import BeautifulSoup


async def search_torrent1337x(movie_type, title):
    if movie_type == 'series':
        category = 'TV'
    else:
        category = 'Movies'

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    title = title.replace('&', 'and')
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://www.1337xx.to/category-search/{title}/{category}/1/', ssl=ssl_context) as req:
            # Read the response content asynchronously
            print('HEREE')
            response_text = await req.text()
    if req.status == 200:
        soup = BeautifulSoup(response_text, 'lxml')
        soup = soup.find('div', class_='box-info')
        soup = soup.find('tbody')
        soup = soup.find_all('a')
        title = title.replace(' ', '.').lower()
        title = title.replace('-', '.')
        links = [f'https://www.1337xx.to{link.get("href")}' for link in soup
                 if title in link.text.lower().replace('-', '.')
                 ]
        print(links)
    return links


async def get_torrent1337x(links):
    torrent_links = []
    for link in links:
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as req:
                # Read the response content asynchronously
                response_text = await req.text()

        soup = BeautifulSoup(response_text, 'lxml')
        soup = soup.find('div', class_="col-9 page-content")
        soup = soup.find('li')
        soup = soup.next
        soup = soup.get('href')
        # some links are magnets(they are the raw torrent file)
        torrent_links.append(soup)

    return torrent_links
