# QFX Scraper

A simple scrapper for [https://qfxcinemas.com](https://qfxcinemas.com) site.


## Usage

```python
from qfx import QFXScraper
scraper = QFXScraper()

# returns all movies listed in QFX's homepage, showing or not showing
movies = scraper.get_movies()


# returns now showing and coming up respectively
print(scraper.showing)
print(scraper.coming_up)
