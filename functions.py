import requests
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import os

def tfpdl_links(title):
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


def tfpd(type, title):
    if type == 'se':
        page = 1
        title = title.replace('-', ' ')
        title = title.replace(' ', '+')
        title = title.replace(':', '')
        session = HTMLSession()
        req = session.get(f'https://tfpdl.is/page/{page}/?s={title}')
    else:
        page = False
        title = title.replace('-', ' ')
        title = title.replace(' ', '+')
        title = title.replace(':', '')
        session = HTMLSession()
        req = session.get(f'https://tfpdl.is/?s={title}+720p')
    links = []
    if page:
        index = 0
        while req.status_code == 200:
            soup = BeautifulSoup(req.text, 'lxml')
            soup = soup.find('div', class_='content')
            soup = soup.find_all('h2', class_='post-title')
            title = title.replace('+', '-')
            length = len(soup) * 4
            for indexx, items in enumerate(soup):
                index = index+1
                yield int(((index / length) * 100))
                soup = items.select(f'a[href^="https://tfpdl.is/{title}"]')
                if soup:
                    links.append(soup[0].get('href'))
                else:
                    pass
            final = tfpdl_links(links)
            page += 1
            title = title.replace('-', '+')
            href = f'https://tfpdl.is/page/{page}/?s={title}+720p'
            req = session.get(href)
            if page == 4:
                yield 'Collecting Data...'
            if page > 4:
                break
        yield final
    else:
        soup = BeautifulSoup(req.text, 'lxml')
        soup = soup.find('div', class_='content')
        soup = soup.find_all('h2', class_='post-title')
        title = title.replace('+', '-')
        length = len(soup)
        index = 0
        for items in soup:
            soup = items.select(f'a[href^="https://tfpdl.is/{title}"]')
            index = index + 1
            yield int(((index / length) * 100))
            if soup:
                links.append(soup[0].get('href'))
            else:
                pass
        final = tfpdl_links(links)
        yield final


def get_torrent1337x(links):
    all_links = []
    for link in links:
        session = HTMLSession()
        req = session.get(link)
        soup = BeautifulSoup(req.text, 'lxml')
        soup = soup.find('div', class_="col-9 page-content")
        soup = soup.find('li')
        soup = soup.next
        soup = soup.get('href')
        all_links.append(soup)
    return all_links


def search_torrent1337x(title):
    if 'se' in title[:2]:
        title = title[2:]
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
        else:
            return False
    else:
        return False


def netnaija(title):
    netnaija_links = []
    title = title.replace('-', ' ')
    title = title.replace(' ', '+')
    title = title.replace(':', '')
    req = requests.get(f'https://www.thenetnaija.net/search?t={title}&folder=videos')
    soup = BeautifulSoup(req.text, 'lxml')
    soup = soup.find('div', id='content')
    soup = soup.find('div', class_='search-results')
    soup = soup.find_all('a')
    if len(soup) == 1:
        netnaija_links.append(soup[0].text)
        netnaija_links.append(soup[0].get('href'))
        return netnaija_links
    title = title.replace('+', '-')
    title = title.lower()
    for links in soup:
        link = links.get('href')
        if title in link:
            netnaija_links.append(links.text)
            netnaija_links.append(link)
    return get_naija(netnaija_links)


def get_naija(links):
    final_links = []
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0',
               'Accept': 'test/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Referer': 'http://www.google.com/'}
    for link in range(len(links)):
        try:
            if 'https' in links[link]:
                req = requests.get(links[link], headers=headers)
                soup = BeautifulSoup(req.text, 'lxml')
                soup = soup.find('div', id='content')
                soup = soup.find('main', class_="video-entry")
                soup = soup.find('div', class_="download-block-con")
                soup = soup.find('a', class_='btn')
                soup = soup.get('href')
                soup = 'https://www.thenetnaija.net' + str(soup)
                final_links.append(soup)
            else:
                final_links.append(links[link])
        except AttributeError as e:
            final_links.append(links[link])
    return final_links


def month_converter(date):
    # date = date.split('-')
    months = {
        '01': 'January',
        '02': 'February',
        '03': 'March',
        '04': 'April',
        '05': 'May',
        '06': 'June',
        '07': 'July',
        '08': 'August',
        '09': 'September',
        '10': 'October',
        '11': 'November',
        '12': 'December'
    }
    start = date[0:4]
    convert = date[5:7]
    end = date[8:]
    converted = months.get(convert, convert)
    converted = end + " " + converted + " " + start
    return converted


def search(query, category, results, page):
    if page:
        return results[page]
    else:
        req = requests.get(f'https://api.themoviedb.org/3/search/{category}?api_key={os.environ.get("api_key")}'
                           f'&language=en-US&query={query}&page=1&include_adult=false')
        req = req.json()['results']
        return req
