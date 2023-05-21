import requests
from bs4 import BeautifulSoup


async def tfpdl_links(title):
    links = []
    for items in range(len(title)):
        url = requests.get(title[items])
        if url:
            soup = BeautifulSoup(url.text, 'lxml')
            link = soup.find('div', class_="content")
            name = link.find('h1', ).text
            ide = link.find('div', class_="entry")
            ide = ide.find('a', class_='button')
            if ide:
                links.append(name)
                links.append(ide.get('href'))
            else:
                ide = link.find('div', class_="entry")
                ide = ide.find_all('a', )
                links.append(name)
                links.append(ide[0].get('href'))
    return links

