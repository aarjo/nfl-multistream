from html.parser import HTMLParser
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
from pprint import pprint
import requests
from pytz import timezone

TIMEZONE = timezone('US/Eastern')

def convertWatchToEmbedUrl(watch):
    beg_index = watch.index('nfl-')
    end_index = watch.index('.html')
    id = int(watch[beg_index+4:end_index])
    
    embed_id = '' if id == 1 else f'-{id}'
    embed_url = f'http://bfst.to/embe/nfl{embed_id}.php'
    return id, embed_url

class NFLGame:
    pass


class DateInfo:
    pass


class NFLParser(HTMLParser):
    curr_year = date.today().year

    def __init__(self):
        HTMLParser.__init__(self)
        self.parsing_game = False
        self.nested_level = 0
        self.curr_game = NFLGame()
        self.all_games = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if self.parsing_game:
                self.nested_level += 1
            else:
                for attr in attrs:
                    if attr[0] == 'href' and 'buff-streamz.com/watch' in attr[1]:
                        self.parsing_game = True
                        self.curr_game = NFLGame()
                        self.date_info = DateInfo()
                        self.curr_game.id, self.curr_game.embed_link = convertWatchToEmbedUrl(attr[1])

    def handle_endtag(self, tag):
        if tag == 'a':
            if self.nested_level == 0:
                if self.parsing_game:
                    self.parsing_game = False
                    full_datetime = self.date_info.date.combine(self.date_info.date, self.date_info.time.time())
                    self.curr_game.date = TIMEZONE.localize(full_datetime)
                    self.all_games.append(self.curr_game)
            else:
                self.nested_level -= 1

    def handle_data(self, data):
        data = data.strip()
        if ' vs ' in data:
            teams = data.split(' vs ')
            self.curr_game.away_team = teams[0]
            self.curr_game.home_team = teams[1]
        elif str(self.curr_year) in data:
            self.date_info.date = datetime.strptime(data, '%Y-%m-%d')
        elif 'EST' in data:
            formatted = data.upper().replace('EST','').strip()
            self.date_info.time = datetime.strptime(formatted, '%I:%M %p')

def _gameHasNotAlreadyEnded(game):
    game_end = game.date + timedelta(hours=4)
    now = datetime.now(TIMEZONE)
    return now < game_end

def getJsonData():
    r = requests.get("http://buff-streamz.com/nfl-streams")
    parser = NFLParser()
    parser.feed(r.text)

    add_test_games = False
    if add_test_games:
        Object = lambda **kwargs: type("Object", (), kwargs)
        parser.all_games.append(Object(home_team='Test 1', away_team='Test Away 1', id= 154, embed_link= 'http://bfst.to/embe/nfl.php', date='1234'))
        parser.all_games.append(Object(home_team='Test 2', away_team='Test Away 2', id= 155, embed_link= 'http://bfst.to/embe/nfl.php', date='1234'))
        parser.all_games.append(Object(home_team='Test 3', away_team='Test Away 3', id= 156, embed_link= 'http://bfst.to/embe/nfl.php', date='1234'))
    
    filtered_games = filter(lambda game :_gameHasNotAlreadyEnded(game), parser.all_games)
    return dict({'data': list(map(lambda game: dict({'id': game.id, 'home_team': game.home_team, 'away_team': game.away_team, 'embed_link': game.embed_link, 'date': game.date}), filtered_games))})
