#!/usr/bin/python3
import argparse
import json, yaml
import os, sys
import pprint
import urllib.request as Rq

pp = pprint.PrettyPrinter()

CONFIG_FILE = 'ow_config.yml'

with open(CONFIG_FILE, 'r') as c:
    config = yaml.load(c, Loader=yaml.CLoader)

weather_url = "https://api.openweathermap.org/data/2.5/weather?q={city}&APPID={token}&units=metric"
pushgateway_url = 'http://{host}:{port}/metrics/job/openweather_exporter'

OW_API_TOKEN = config['api_token']
CITIES = config['cities']  # for now
PUSHGW_ENDPOINT = config["pushgw_endpoint"]["hostname"] # FIXME set default to localhost?
PUSHGW_PORT = config["pushgw_endpoint"]["port"]         # FIXME set default 9091
elastic_document = (
'''# TYPE weather_info gauge\n'''
'''# TYPE weather_return_code gauge\n'''
'''# TYPE weather_temperature gauge\n'''
'''# TYPE weather_humidity gauge\n'''
'''# TYPE weather_pressure gauge\n'''
'''# TYPE weather_wind_speed gauge\n'''
'''# TYPE weather_wind_direction gauge\n'''
'''# TYPE weather_clouds_percent gauge\n'''
'''# TYPE weather_sun_epoch gauge\n'''
'''# TYPE weather_rain_1h gauge\n'''
'''# TYPE weather_snow_1h gauge\n'''
)

for city in CITIES:
    ## get current weather
    with Rq.urlopen(weather_url.format(city=city, token=OW_API_TOKEN).replace(' ', '+')) as f:
        msg = json.loads(f.read())

    city_name = msg['name']
    
    elastic_document += (
    f'''weather_info{{location="{city_name}",country="{msg['sys']['country']}",weatherid="{msg['weather'][0]['id']}",weathermain="{msg['weather'][0]['main']}",weatherdesc="{msg['weather'][0]['description']}"}} {msg['id']}\n'''
    f'''weather_return_code{{name="{city_name}"}} {msg['cod']}\n'''
    f'''weather_temperature{{name="{city_name}",type="current"}} {msg['main']['temp']}\n'''
    f'''weather_humidity{{name="{city_name}"}} {msg['main']['humidity']}\n'''
    f'''weather_pressure{{name="{city_name}",level="ground"}} {msg.get('main', {}).get('grnd_level', msg['main']['pressure'])}\n'''
    f'''weather_pressure{{name="{city_name}",level="sea"}} {msg.get('main', {}).get('sea_level', msg['main']['pressure'])}\n'''
    f'''weather_wind_speed{{name="{city_name}"}} {msg['wind']['speed']}\n'''
    f'''weather_wind_direction{{name="{city_name}"}} {msg['wind']['deg']}\n'''
    f'''weather_clouds_percent{{name="{city_name}"}} {msg['clouds']['all']}\n'''
    f'''weather_sun_epoch{{name="{city_name}",change="sunrise"}} {msg['sys']['sunrise']}\n'''
    f'''weather_sun_epoch{{name="{city_name}",change="sunset"}} {msg['sys']['sunset']}\n'''
    f'''weather_rain_1h{{name="{city_name}"}} {msg.get('rain', {}).get('1h', 0)}\n'''
    f'''weather_snow_1h{{name="{city_name}"}} {msg.get('snow', {}).get('1h', 0)}\n'''
    )
    ## TODO add coordinates
    ## TODO add weather picture id

## preparing binary data for urllib
jdata = elastic_document.encode('utf-8')

## posting document
elastic_rq = Rq.Request(pushgateway_url.format(host=PUSHGW_ENDPOINT, port=PUSHGW_PORT), data=jdata, method='POST')
elastic_rq.add_header('Content_Type', 'form-data')
with Rq.urlopen(elastic_rq) as f:
    resp = f.read()
