import os
import requests
import asyncio
import io
import urllib.request
api_key = os.environ.get('tmdbApiKey')


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


async def search(query, category="movie"):
    req = requests.get(f'https://api.themoviedb.org/3/search/{category}?api_key={api_key}'
                       f'&language=en-US&query={query}&page=1&include_adult=false')
    req = req.json()['results']
    return req


def get_movie_type(movie: dict):
    """Gets the type of the movie """
    return ['title', 'release_date'] if movie.get('title') else ['name', 'first_air_date']


async def get_raw_image(movie_poster_url: str) -> io.BytesIO | None:
    # Get the image for the movie asynchronously
    loop = asyncio.get_running_loop()
    try:
        with urllib.request.urlopen(movie_poster_url) as response:
            # Read the response content asynchronously and write it to an io.BytesIO object
            file_obj = io.BytesIO(await loop.run_in_executor(None, response.read))

        return file_obj
    except urllib.error.HTTPError:
        return None


