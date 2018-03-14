import re
import os
from requests_html import HTMLSession


EVENT_ID_PATTERN = re.compile(r".*EventID=(?P<event_id>)\d{4,8}")
BASE_URL = os.environ.get("BASE_URL", "https://qfxcinemas.com")


class Movie:

    def __init__(self, event_id, detail, ticket,
                 poster, title, type, session, movie_date=None):
        self.event_id = event_id
        self.detail_url = detail
        self.tickets = ticket
        self.poster = poster
        self.title = title
        self.type = type
        self.session = session

    def __repr__(self):
        return f"<Movie: {self.title}>"

    @property
    def detail(self):
        detail = {}

        if self.detail_url:
            r = self.session.get(self.detail_url)

            # r.html.find("Non")

        return detail


class QFXScraper:

    def __init__(self):
        self.showing = None
        self.coming_up = None
        self.session = HTMLSession()

    def get_movies(self):
        r = self.session.get(BASE_URL)
        now_showing, coming_soon = r.html.find(".content .movies")

        self.showing = self._get_movies(now_showing, True)
        self.coming_up = self._get_movies(coming_soon, False)
        return self.showing + self.coming_up

    def _get_movies(self, movies_container_element, is_coming_soon):
        movies = []
        for movie in movies_container_element.find(".movie"):
            detail = movie.find("a", first=True).attrs["href"]
            ticket = movie.find("a.ticket", first=True)

            data = {
                "detail": detail,
                "ticket": ticket.attrs["href"] if ticket else None,
                "poster": movie.find("img.img-b", first=True).attrs["src"],
                "title": movie.find("h4.movie-title", first=True).text,
                "type": movie.find("p.movie-type", first=True).text,
                "session": self.session,
            }

            if is_coming_soon:
                movie_date = movie.find("p.movie-date", first=True)
                if movie_date:
                    data["movie_date"] = movie_date.text

            match = EVENT_ID_PATTERN.match(detail)
            if match:
                data["event_id"] = match.group()
                movie = Movie(**data)
                movies.append(movie)
            else:
                print("Something is wrong with {}".format(detail))
        return movies

    def __repr__(self):
        showing, coming = len(self.showing), len(self.coming_up)
        return f"Showing: {showing}, Coming up: {coming}"


if __name__ == "__main__":
    scraper = QFXScraper()
    scraper.get_movies()

    print("QFX scraper: {}".format(scraper))
    print("Showing: ", scraper.showing)
    print("Coming up: ", scraper.coming_up)
