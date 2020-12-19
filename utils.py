from movie_search import OkkoSearcher, KinoPoiskSearcher, FilmRuSearcher


def get_platform_searcher(platform: str):
    """Get searcher from string"""
    if platform == 'Ökko':
        return OkkoSearcher()
    elif platform == 'KinoPoisk':  # TODO: add another platforms
        return KinoPoiskSearcher()
    elif platform == 'Film.Ru':  # TODO: add another platforms
        return FilmRuSearcher()
    else:  # TODO: add another platforms
        return OkkoSearcher()