#!/usr/bin/python3
import os
import urllib.request as Rq
import json
import pprint

pp = pprint.PrettyPrinter()

API_TOKEN_FILE = '.token'
INDEX_NAME = 'o_weather_valday'
CITY_ID = 477301

weather_url = "https://api.openweathermap.org/data/2.5/weather?id={city}&APPID={token}&units=metric"
elastic_url = "http://localhost:9200/{index}/_doc/"

def get_token():
    """ This function tries to get OpenWeather API token from environment variable
        or from .token file in the same directory as the script"""
    token_path = os.path.join(os.path.dirname(__file__), API_TOKEN_FILE)
    _TOKEN = os.getenv('OW_API_TOKEN')
    if _TOKEN:
        return _TOKEN
    elif os.path.exists(token_path):
        with open(token_path, 'r') as t:
            _TOKEN = t.read()
        return _TOKEN
    else:
        return None

## try to get API token
OW_API_TOKEN = get_token()

if OW_API_TOKEN:
    ## get current weather
    with Rq.urlopen(weather_url.format(city=CITY_ID, token=OW_API_TOKEN)) as f:
        msg = json.loads(f.read())

    ## document computation
    elastic_document = {
      "location":       msg['coord'],
      "weather_id":     msg['weather'][0]['id'],
      "weather_main":   msg['weather'][0]['main'],
      "weather_descr":  msg['weather'][0]['description'],
      "temp":           msg['main']['temp'],
      "humidity":       msg['main']['humidity'],
      "pressure_sea":   msg['main']['sea_level'] / 1.33322387415,
      "pressure_gnd":   msg['main']['grnd_level'] / 1.33322387415,
      "wind_speed":     msg['wind']['speed'],
      "wind_deg":       msg['wind']['deg'],
      "clouds":         msg['clouds']['all'],
      "rain_1h":        msg.get('rain', {}).get('1h', 0),
      "rain_3h":        msg.get('rain', {}).get('3h', 0),
      "snow_1h":        msg.get('snow', {}).get('1h', 0),
      "show_3h":        msg.get('snow', {}).get('3h', 0),
      "timestamp":      msg['dt'],
      "country":        msg['sys']['country'],
      "sunrise":        msg['sys']['sunrise'],
      "sunset":         msg['sys']['sunset'],
      "timezone":       msg['timezone'],
      "city_id":        msg['id'],
      "city_name":      msg['name']
    }

    ## preparing binary data for urllib
    jdata = json.dumps(elastic_document).encode('utf-8')

    ## posting document
    elastic_rq = Rq.Request(elastic_url.format(index=INDEX_NAME), data=jdata, method='POST')
    elastic_rq.add_header('Content-Type', 'application/json; charset=utf-8')
    with Rq.urlopen(elastic_rq) as f:
        resp = json.loads(f.read())

    pp.pprint(resp)
else:
    # TODO: implement some notification
    print("Couldn't get API token!")
