from requests_html import HTMLSession
from bs4 import BeautifulSoup


async def search_torrent1337x(movie_type, title):
    if movie_type == 'series':
        category = 'TV'
    else:
        category = 'Movies'
    title = title.replace('&', 'and')
    links_list = []
    session = HTMLSession()
    req = session.get(f'https://www.1337xx.to/category-search/{title}/{category}/1/')
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, 'lxml')
        soup = soup.find('div', class_='box-info')
        soup = soup.find('tbody')
        soup = soup.find_all('a')
        title = title.replace(' ', '.').lower()
        title = title.replace('-', '.')
        for links in soup:
            link = links.text.lower().replace('-', '.')
            if title in link:
                link = links.get('href')
                link = 'https://www.1337xx.to' + link
                links_list.append(link)
        if links_list:
            return links_list
    return False


async def get_torrent1337x(links):
    torrent_links = []
    for link in links:
        session = HTMLSession()
        req = session.get(link)
        soup = BeautifulSoup(req.text, 'lxml')
        soup = soup.find('div', class_="col-9 page-content")
        soup = soup.find('li')
        soup = soup.next
        soup = soup.get('href')
        torrent_links.append(soup)
    return torrent_links
