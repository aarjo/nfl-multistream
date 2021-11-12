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


class TeamInfo:
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
                        self.curr_game.home_team = TeamInfo()
                        self.curr_game.away_team = TeamInfo()
                        self.date_info = DateInfo()
                        self.curr_game.id, self.curr_game.embed_link = convertWatchToEmbedUrl(
                            attr[1])

    def handle_endtag(self, tag):
        if tag == 'a':
            if self.nested_level == 0:
                if self.parsing_game:
                    self.parsing_game = False
                    full_datetime = self.date_info.date.combine(
                        self.date_info.date, self.date_info.time.time())
                    self.curr_game.date = TIMEZONE.localize(full_datetime)
                    self.all_games.append(self.curr_game)
            else:
                self.nested_level -= 1

    def handle_data(self, data):
        data = data.strip()
        if ' vs ' in data:
            teams = data.split(' vs ')
            self.curr_game.away_team.name = teams[0]
            self.curr_game.home_team.name = teams[1]
        elif str(self.curr_year) in data:
            self.date_info.date = datetime.strptime(data, '%Y-%m-%d')
        elif 'EST' in data:
            formatted = data.upper().replace('EST', '').strip()
            self.date_info.time = datetime.strptime(formatted, '%I:%M %p')


def _gameHasNotAlreadyEnded(game):
    game_end = game.date + timedelta(hours=4)
    now = datetime.now(TIMEZONE)
    return now < game_end


def _parseBovadaData(game_list):
    bovada_data = requests.get(
        'https://www.bovada.lv/services/sports/event/v2/events/A/description/football/nfl').json()[0]['events']
    for event in bovada_data:
        for game in game_list:
            if game.home_team.name in event['description'] and game.away_team.name in event['description']:
                outcomes = event['displayGroups'][0]['markets'][0]['outcomes']
                for outcome in outcomes:
                    odds = float(outcome['price']['decimal'])
                    if outcome['description'] == game.home_team.name:
                        game.home_team.odds = odds
                    elif outcome['description'] == game.away_team.name:
                        game.away_team.odds = odds


def getJsonData():
    r = requests.get("http://buff-streamz.com/nfl-streams")
    parser = NFLParser()
    parser.feed(r.text)

    _parseBovadaData(parser.all_games)

    add_test_games = False
    if add_test_games:
        Object = lambda **kwargs: type("Object", (), kwargs)
        parser.all_games.append(Object(home_team=Object(name='Test Home 1', odds=1.23456), away_team=Object(name='Test Away 1', odds=1.23456),
                                id=154, embed_link='http://bfst.to/embe/nfl.php', date=datetime.now(TIMEZONE)))
        parser.all_games.append(Object(home_team=Object(name='Test Home 2', odds=1.23456), away_team=Object(name='Test Away 2', odds=1.23456),
                                id=155, embed_link='http://bfst.to/embe/nfl.php', date=datetime.now(TIMEZONE)))
        parser.all_games.append(Object(home_team=Object(name='Test Home 3', odds=1.23456), away_team=Object(name='Test Away 3', odds=1.23456),
                                id=156, embed_link='http://bfst.to/embe/nfl.php', date=datetime.now(TIMEZONE)))

    filtered_games = filter(_gameHasNotAlreadyEnded, parser.all_games)
    return dict({'data': list(map(lambda game: dict({'id': game.id, 'home_team': {'name': game.home_team.name, 'odds': game.home_team.odds if hasattr(game.home_team, 'odds') else None}, 'away_team': {'name': game.away_team.name, 'odds': game.away_team.odds if hasattr(game.away_team, 'odds') else None}, 'embed_link': game.embed_link, 'date': game.date}), filtered_games))})


getJsonData()
