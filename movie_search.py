import abc
import aiohttp
import typing as tp

from aiogram import types
from bs4 import BeautifulSoup
from Levenshtein import distance as levenshtein_distance
from typing import NamedTuple


class OkkoMovieReport(NamedTuple):
    title: tp.Optional[str] = None
    alternative_title: tp.Optional[str] = None
    poster_link: tp.Optional[str] = None
    description: tp.Optional[str] = None
    movie_link: tp.Optional[str] = None

class KinoPoiskMovieReport(NamedTuple):
    title: tp.Optional[str] = None
    year: tp.Optional[str] = None
    film_link: tp.Optional[str] = None

class FilmRuMovieReport(NamedTuple):
    title: tp.Optional[str] = None
    rating: tp.Optional[str] = None
    poster: tp.Optional[str] = None
    link: tp.Optional[str] = None


class OkkoBaseSearcher:
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    async def get_link_from_message(message: types.message) -> str:
        """Method to obtain movie link from user message"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    async def get_movie_info_from_link(link: str) -> OkkoMovieReport:
        """Method to obtain movie info from link (e.g. name, description)"""
        raise NotImplementedError

    @staticmethod
    def title_matches(message_text: str, title: str, lev_distance: int = 3) -> bool:
        """Calculate levenshtein distance between two strings"""
        return levenshtein_distance(message_text, title) < lev_distance

    async def __call__(self, message: types.message) -> OkkoMovieReport:
        link = await self.get_link_from_message(message)
        if link == "":
            return OkkoMovieReport()
        report = await self.get_movie_info_from_link(link)
        alternative_title_match = False
        title_match = False

        if report.title is not None:
            title_match = self.title_matches(message.text.lower(), report.title.lower())
        if report.alternative_title is not None:
            alternative_title_match = self.title_matches(message.text.lower(), report.alternative_title.lower())
        if title_match or alternative_title_match:
            return report
        return OkkoMovieReport()







class OkkoSearcher(OkkoBaseSearcher):
    @staticmethod
    async def get_link_from_message(message: types.message) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://okko.tv/search/{message.text.lower()}') as response:
                search_html = await response.text()

        soup = BeautifulSoup(search_html, "lxml")

        # check that page is found
        for paragraph in soup.findAll('p'):
            if 'Увы, мы ничего не нашли' in paragraph.getText():
                return ""

        link: str = ""
        for val in soup.findAll('a'):
            if '/movie/' in val.get('href'):
                link = 'https://okko.tv' + val.get('href')
                break
        return link

    @staticmethod
    async def get_movie_info_from_link(movie_link: str) -> OkkoMovieReport:
        async with aiohttp.ClientSession() as session:
            async with session.get(movie_link) as response:
                movie_html = await response.text()
        soup_movie = BeautifulSoup(movie_html, "lxml")

        # title
        title = soup_movie.find("h1", {"class": "LOjIO"})
        if title is not None:
            title = title.getText()
            if title[0] == '«' and title.rfind('»') != -1:
                title = title[1: title.rfind('»')]

        alternative_title = soup_movie.find("h2", {"class": "_1lODb"})
        if alternative_title is not None:
            alternative_title = alternative_title.getText()

        # poster
        poster_link = soup_movie.find("source", {"type": "image/jpeg"})
        if poster_link is not None:
            poster_link = "https://" + poster_link.get("srcset").split()[0][2:]

        # description
        description = None
        description_paragraph = soup_movie.find('p', {"class": "_3Zh7s"})
        if description_paragraph is not None:
            description_span = description_paragraph.find("span")
            if description_span is not None:
                description = description_span.getText()
        if description is not None:
            description = " ".join([x for x in description.split(' ') if x][:50]) + '...'
        return OkkoMovieReport(title, alternative_title, poster_link, description, movie_link)





class KinoPoiskBaseSearcher:
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    async def get_info(message: types.message) -> KinoPoiskMovieReport:
        """Method to obtain movie link from user message"""
        raise NotImplementedError

    @staticmethod
    def title_matches(message_text: str, title: str, lev_distance: int = 3) -> bool:
        """Calculate levenshtein distance between two strings"""
        return levenshtein_distance(message_text, title) < lev_distance

    async def __call__(self, message: types.message) -> KinoPoiskMovieReport:
        report = await self.get_info(message)

        title_match = False

        if report.title is not None:
            title_match = self.title_matches(message.text.lower(), report.title.lower())
        if title_match:
            return report
        return KinoPoiskMovieReport()



class KinoPoiskSearcher(KinoPoiskBaseSearcher):
    @staticmethod
    async def get_info(message: types.message) -> KinoPoiskMovieReport:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.kinopoisk.ru/index.php?kp_query={message.text.lower()}') as response:
                search_html = await response.text()

        soup = BeautifulSoup(search_html, "lxml")

        if len(soup.findAll('p')) == 0:
            return KinoPoiskMovieReport()
        if 'Скорее всего, вы ищете' in soup.findAll('p')[0].getText():
            film_link = 'https://www.kinopoisk.ru' + soup.findAll('p')[1].findAll('a')[0].get('data-url')
            name = soup.findAll('p')[2].findAll('a')[0].getText()
            year = soup.findAll('p')[2].findAll('span')[0].getText()
            return KinoPoiskMovieReport(name, year, film_link)




class FilmRuBaseSearcher:
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    async def get_info(message: types.message) -> FilmRuMovieReport:
        """Method to obtain movie link from user message"""
        raise NotImplementedError

    @staticmethod
    def title_matches(message_text: str, title: str, lev_distance: int = 3) -> bool:
        """Calculate levenshtein distance between two strings"""
        return levenshtein_distance(message_text, title) < lev_distance

    async def __call__(self, message: types.message) -> FilmRuMovieReport:
        report = await self.get_info(message)

        title_match = False

        if report.title is not None:
            title_match = self.title_matches(message.text.lower(), report.title.lower())
        if title_match:
            return report
        return FilmRuMovieReport()



class FilmRuSearcher(FilmRuBaseSearcher):
    @staticmethod
    async def get_info(message: types.message) -> FilmRuMovieReport:
        link = 'https://www.film.ru/search/result?text='
        for w in message.text.lower().split():
            link += w + '+'
        link += '&type=all'
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                search_html = await response.text()

        soup = BeautifulSoup(search_html, "lxml")

        if len(soup.findAll('div')) < 54:
            return FilmRuMovieReport()
        else:
            film = soup.findAll('div')[32].findAll('a')[0]
            poster = film.findAll('img')[0].get('src')
            title = film.findAll('strong')[0].getText()
            rating = film.findAll('strong')[1].getText()
            link = 'https://www.film.ru' + film.get('href')
            return FilmRuMovieReport(title, rating, poster, link)
