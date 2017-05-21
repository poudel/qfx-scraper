'''
A hotwired script to scrap movies data from qfx cinemas website
and notify with email if anything changes. Just for fun! Still a lot to do.

TODO:
    - unit testing
    - cli using click framework
    - web interface using bottle.py
    - installation via pip
    - email notification recipients in database
    - event participation confirmation by replying to notification email
'''
import os
import time
import re
import smtplib
import configparser
import requests
from email.mime.text import MIMEText
from itertools import chain
from datetime import datetime
from collections import defaultdict
from texttable import Texttable
from dateutil.parser import parse
from bs4 import BeautifulSoup
from peewee import *


ROOT_URL = 'http://www.qfxcinemas.com/'
NOW_SHOWING_URL = '{root_url}Home/GetMovieDetails?EventID={event_id}'
COMING_SOON_URL = '{root_url}Home/GetComingSoonMovieDetails?EventID={event_id}'
BOOKING_URL = '{root_url}Home/GetTicketBookDetail?EventID={event_id}'
NOW_SHOWING, COMING_SOON, SHOW_OVER = 1, 2, 3
STATUS_DISPLAY = {NOW_SHOWING: 'Now Showing', COMING_SOON: 'Coming Soon', SHOW_OVER: 'Show Over'}
THROTTLE_TIME = 1
HOME_DIR = os.path.expanduser('~')
WORKING_DIR = os.path.join(HOME_DIR, '.qfx')
CONFIG_PATH = os.path.join(WORKING_DIR, 'config')
DB_PATH = os.path.join(WORKING_DIR, "movies.db")

if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

DB_EXISTS = os.path.exists(DB_PATH)


db = SqliteDatabase(DB_PATH)
event_id_pattern = re.compile(r'.*\?EventID=(?P<event_id>\d+)')


if os.path.exists(CONFIG_PATH):
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    email_config = config['email']
else:
    email_config = None


def _get_movies_inside(portion, status):
    '''
    Extract movie data from a DOM portion
    '''
    movies = []
    _movies = portion.find_all('div', 'movie')
    for movie in _movies:
        event = {}
        detail_href = movie.find('div', 'movie-poster').find('a').get('href')
        match = event_id_pattern.match(detail_href)
        event_id = match.groupdict()['event_id']

        event = {
            'event_id': int(event_id),
            'title': movie.find('h4', 'movie-title').text,
            'movie_type': movie.find('p', 'movie-type').text,
            'status': status,
        }

        format_kwargs = {'root_url': ROOT_URL, 'event_id': event_id}

        if status == NOW_SHOWING:
            detail_url = NOW_SHOWING_URL.format(**format_kwargs)
        else:
            detail_url = COMING_SOON_URL.format(**format_kwargs)

        # get the detail of the movie
        response = requests.get(detail_url)
        if response.status_code == 200:
            detail_soup = BeautifulSoup(response.content, 'html.parser')
            movie_info = detail_soup.find('div', 'movie-info').find_all('p')

            event['release_date'] = parse(movie_info[0].find_all('span')[1].text).date()
            event['run_time'] = movie_info[1].find_all('span')[1].text
            event['director'] = movie_info[2].find_all('span')[1].text
            event['genre'] = movie_info[3].find_all('span')[1].text
            event['cast'] = movie_info[4].find_all('span')[1].text
        else:
            # TODO: notify
            pass

        movies.append(event)
        time.sleep(THROTTLE_TIME)
    return movies


def fetch_movies():
    response = requests.get(ROOT_URL)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        _movies = soup.find_all('div', 'movies')
        # i'm not sure if we need to distinguish between now
        # showing and coming soon, but..
        now_showing, coming_soon = _movies[0], _movies[1]
        return (_get_movies_inside(now_showing, NOW_SHOWING),
                _get_movies_inside(coming_soon, COMING_SOON))
    else:
        pass
        # TODO: notify 
    return ([], [])


class Movie(Model):
    title = CharField()
    release_date = DateField()
    created_at = DateTimeField()
    movie_type = CharField()
    event_id = IntegerField(unique=True)
    status = IntegerField()
    run_time = CharField()
    director = CharField()
    genre = CharField()
    cast = CharField()

    class Meta:
        database = db

    def __str__(self):
        return self.title

    def get_status_display(self):
        return STATUS_DISPLAY[self.status]


def update_movies():
    fetched = chain(*fetch_movies())
    changed_items = defaultdict(dict)
    new_items = []
    site_items = set()

    for show_event in fetched:
        event_id = show_event.pop('event_id')
        defaults = show_event.copy()
        defaults['created_at'] = datetime.now()
        event, created = Movie.get_or_create(event_id=event_id, defaults=defaults)

        site_items.add(event.event_id)

        if not created:
            for field_name, value in show_event.items():
                saved_value = getattr(event, field_name)
                if saved_value != value:
                    changed_items[event].update({
                        field_name: [value, saved_value]
                    })

                    setattr(event, field_name, value)
            event.save()
        else:
            new_items.append(event)

        # delete items that are not in the qfx website
        to_delete = Movie.delete().where(Movie.event_id.not_in(site_items))
    return new_items, changed_items


def save_and_notify():
    new, changed = update_movies() 
    new = Movie.select() 

    if new:
        ntable = Texttable()
        new_rows = [
            ["Title", "Type", "Date", "Run Time", "Director", "Genre", "Cast", "Status"]
        ]
        for item in new:
            new_rows.append([
                item.title, item.movie_type, item.release_date.isoformat(),
                item.run_time, item.director, item.genre, item.cast, item.get_status_display()
            ])
        ntable.add_rows(new_rows)
        send_email('New movies have arrived!\n{}\nThank you!'
                   .format(ntable.draw()))

    if changed:
        ctable = Texttable()
        changed_rows = [["Title", "Changes", "Date", "Status"]]
        for event, changes in changed.items():
            change_col = "\n".join([
                "{} => {}".format(c[1], c[0])
                for c in changes
            ])
            changed_rows.append([
                event.title, 
                change_col,
                event.release_date.isoformat(),
                event.get_status_display()
            ])
        ctable.add_rows(changed_rows)
        send_email('Some changes in saved movies!\n{}\nThank you!'
                   .format(ctable.draw()))


def notify_admin(message):
    return send_email(message, subject='MovieQuest: Admin', only_admin=True)


def send_email(body, subject=None, only_admin=False):
    if not email_config:
        print('no email')
        return False

    from_address = email_config['from_address']

    if only_admin:
        to_address = [email_config['admin']]
    else:
        to_address = email_config['recipients'].split(',')

    print(to_address)

    server = smtplib.SMTP('{smtp_host}:{smtp_port}'.format(**email_config))
    server.ehlo()
    server.starttls()
    server.login(email_config['username'], email_config['password'])

    message = MIMEText(body)
    message['Subject'] = subject or 'MovieQuest'
    message['From'] = email_config['from_address']
    message['To'] = ', '.join(to_address)

    server.sendmail(from_address, to_address, message.as_string())
    server.quit()


if __name__ == '__main__':
    if not DB_EXISTS:
        db.connect()
        db.create_tables([Movie])

    save_and_notify()
