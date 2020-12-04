import random
from datetime import datetime
from typing import Any, Dict, List

import grequests
from bs4 import BeautifulSoup
from requests import Response

from user_agents import USER_AGENTS  # type: ignore

_requests_at_time = 3
_headers = {
    'User-Agent': random.choice(USER_AGENTS)
}

month_num_mapping = {
    'января': 1,
    'февраля': 2,
    'марта': 3,
    'апреля': 4,
    'мая': 5,
    'июня': 6,
    'июля': 7,
    'августа': 8,
    'сентября': 9,
    'октября': 10,
    'ноября': 11,
    'декабря': 12
}


def async_get(urls: List[str]) -> List[Response]:
    """
        Make GET requests to provided URL list asynchronously.
    """

    gen = (grequests.get(url, headers=_headers) for url in urls)
    return grequests.map(gen, size=_requests_at_time)


def extract_authors_info(page_urls: List[str]) -> List[Dict[str, Any]]:
    """
        Get and parse info about authors by provided links
    """

    for i, url in enumerate(page_urls):
        if not url.endswith('ob-avtore/'):
            page_urls[i] = url + 'ob-avtore/'

    responses = async_get(page_urls)
    authors = []

    for response in responses:
        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('div', {'class': 'author_name'}).text

        bio = soup.find('div', {'class': 'person-page__html'})
        if bio is not None:
            bio = bio.get_text(separator='\n')

        photo_path = soup.find('div', {'class': 'biblio_author_image'})
        photo_path = photo_path.find('img')['src']
        if not photo_path.startswith('https://'):
            photo_path = 'https://litres.ru' + photo_path

        authors.append({
            'name': name,
            'bio': bio,
            'photo_path': photo_path
        })

    return authors


def parse_date(pretty: str) -> datetime:
    day, month, year = pretty.split()

    return datetime(
        day=int(day),
        month=month_num_mapping[month],
        year=int(year)
    )


def extract_books_info(page_urls: List[str]) -> List[Dict[str, Any]]:
    """
        Get and parse info about books by provided links
    """

    responses = async_get(page_urls)
    books = []

    for response in responses:
        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('div', {'class': 'biblio_book_name'})
        name = next(name.stripped_strings)

        publish_date = soup.find('strong', string='Дата выхода на ЛитРес:')
        publish_date = publish_date.next_sibling
        publish_date = parse_date(publish_date)

        preamble = soup.find('div', {'class': 'biblio_book_descr_publishers'})
        if preamble is not None:
            preamble = preamble.get_text(separator='\n')

        cover_path = soup.find('meta', {'property': 'og:image'})['content']

        authors = soup.find('div', {'class': 'biblio_book_author'})
        authors = authors.find_all('a')
        authors = extract_authors_info(['https://litres.ru' + link['href']
                                        for link in authors])

        tags = soup.find('li', {'class': 'tags_list'})
        if tags is not None:
            tags = tags.find_all('a', {'class': 'biblio_info__link'})
            tags = [{'name': tag.text.capitalize()} for tag in tags]
        else:
            tags = []

        genres = soup.find('strong', string='Жанр:').parent
        genres = genres.find_all('a', {'class': 'biblio_info__link'})
        genres = [{'name': genre.text.capitalize()} for genre in genres]

        # But there may be multiple series...
        series = soup.find('div', {'class': 'biblio_book_sequences'})
        if series is not None:
            series = series.find('a', {'class': 'biblio_book_sequences__link'})
            series = series.text

        books.append({
            'name': name,
            'rating_sum': 0,
            'rating_num': 0,
            'publish_date': publish_date,
            'preamble': preamble,
            'cover_path': cover_path,
            'authors': authors,
            'tags': tags,
            'genres': genres,
            'series': series
        })

    return books


if __name__ == '__main__':
    print('Sorry, but crawler is not still implemented :(')
