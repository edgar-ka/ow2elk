import os
import urllib.request as Rq
import json
import boto3

API_TOKEN_FILE = '.token'
INDEX_NAME = 'o_weather_valday'
AWS_ELK_DOMAIN = 'ow2elk'
CITY_ID = 477301

ELK_ENDPOINT = os.getenv('ELK_ENDPOINT')
if not ELK_ENDPOINT:
    cl = boto3.client('es')
    ELK_ENDPOINT = cl.describe_elasticsearch_domain(DomainName=AWS_ELK_DOMAIN)['DomainStatus']['Endpoints']['vpc']

weather_url = "https://api.openweathermap.org/data/2.5/weather?id={city}&APPID={token}&units=metric"
elastic_url = "http://"+ELK_ENDPOINT+"/{index}/_doc/"


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


def lambda_handler(event, context):
    ## get current weather
    with Rq.urlopen(weather_url.format(city=CITY_ID, token=get_token())) as f:
        msg = json.loads(f.read())

    ## document computation
    elastic_document = {
      "location":       msg['coord'],
      "weather_id":     msg['weather'][0]['id'],
      "weather_main":   msg['weather'][0]['main'],
      "weather_descr":  msg['weather'][0]['description'],
      "temp":           msg['main']['temp'],
      "humidity":       msg['main']['humidity'],
      "pressure_sea":   msg['main']['sea_level'] / 1.33322387415,  # hPa->mmHg
      "pressure_gnd":   msg['main']['grnd_level'] / 1.33322387415, # hPa->mmHg
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

    return resp