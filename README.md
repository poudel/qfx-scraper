# QFX Scraper

A simple scrapper for [https://qfxcinemas.com](https://qfxcinemas.com) site.


## Usage

Install the `requests-html` by running:

```bash
pipenv install requests-html
```

Now you can test the scraper.

```python

>>> from qfx import QFXScraper
>>> scraper = QFXScraper()
>>> scraper.get_movies()
[<Movie: Red Sparrow>, <Movie: Pari>, <Movie: 3D: Black Panther>, <Movie: The Hurricane Heist>, <Movie: Mangalam>, <Movie: Gaja Baja>, <Movie: Hurray>, <Movie: A League of Their Own>, <Movie: Black Panther>, <Movie: Tomb Raider>, <Movie: 3D: Tomb Raider>, <Movie: Panchayat>, <Movie: Raid>, <Movie: Shatru Gate>, <Movie: Hichki>, <Movie: Baaghi 2>]

>>> # let's see now showing
>>> scraper.showing
[<Movie: Red Sparrow>, <Movie: Pari>, <Movie: 3D: Black Panther>, <Movie: The Hurricane Heist>, <Movie: Mangalam>, <Movie: Gaja Baja>, <Movie: Hurray>, <Movie: A League of Their Own>, <Movie: Black Panther>]

>>> # similarly, coming soon
>>> scraper.coming_up
[<Movie: Tomb Raider>, <Movie: 3D: Tomb Raider>, <Movie: Panchayat>, <Movie: Raid>, <Movie: Shatru Gate>, <Movie: Hichki>, <Movie: Baaghi 2>]
```
