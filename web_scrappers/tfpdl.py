import aiohttp
import requests
from bs4 import BeautifulSoup


async def download_links(movie_urls: list):
    """Fetches and get the actual download button for each movie item found in the search results"""
    links = []
    for item in movie_urls:
        url = requests.get(item)
        if url:
            soup = BeautifulSoup(url.text, 'lxml')
            link = soup.find('div', class_="content")
            name = link.find('h1', ).text
            ide = link.find('div', class_="entry")
            ide = ide.find('a', class_='button')
            if ide:
                links.append({'title': name, 'url': ide.get('href')})
            else:
                ide = link.find('div', class_="entry")
                ide = ide.find_all('a', )
                links.append({'title': name, 'url': ide[0].get('href')})
    return links


async def get_page(page_url: str):
    """Gets a page of any link asynchronous"""
    async with aiohttp.ClientSession() as session:
        async with session.get(page_url) as req:
            # Return the request object
            response = (await req.text(), req.status)
            return response


async def tfpdl(download_type, title):
    """Scrapes/searches https://tfpdl.is/ for movie links based on the given title"""
    title = title.replace('-', ' ').replace(' ', '+').replace(':', '')
    page = 0
    page, link = (1, f'https://tfpdl.is/page/{page}/?s={title}')\
        if download_type == "series" else (None, f'https://tfpdl.is/?s={title}+720p')

    # get the page given the url
    response_text, status = await get_page(link)
    links = []

    # evaluates to true if the search query isn't a series
    if page:

        # scrapes 4 pages of search result
        index = 0
        while status == 200:
            # this loop runs while the req is still valid
            soup = BeautifulSoup(response_text, 'lxml')
            soup = soup.find('div', class_='content')
            soup = soup.find_all('h2', class_='post-title')
            title = title.replace('+', '-')
            length = len(soup) * 4
            for item in soup:
                index += 1

                # yields a number, acts like a status/progress counter
                yield int(((index / length) * 100))

                # select the links that match this pattern
                soup = item.select(f'a[href^="https://tfpdl.is/{title}"]')
                if soup:
                    links.append(soup[0].get('href'))

            # pass the links list to get each download button of the items
            final = await download_links(links)
            page += 1
            title = title.replace('-', '+')
            href = f'https://tfpdl.is/page/{page}/?s={title}+720p'

            # send  a new request to the website
            response_text, status = await get_page(href)
            if page == 4:
                yield 'Collecting Data...'
            if page > 4:
                # terminate the loop 4 pages maximum!
                break

        # send the final results
        yield final
    else:
        soup = BeautifulSoup(response_text, 'lxml')
        soup = soup.find('div', class_='content')
        soup = soup.find_all('h2', class_='post-title')
        title = title.replace('+', '-')
        length = len(soup)
        index = 0

        for item in soup:
            soup = item.select(f'a[href^="https://tfpdl.is/{title}"]')
            index += 1
            yield int(((index / length) * 100))
            if soup:
                links.append(soup[0].get('href'))
        final = await download_links(links)
        yield final
