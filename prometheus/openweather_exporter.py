#!/usr/bin/python3
import os, sys
import urllib.request as Rq
import json, yaml
import pprint

pp = pprint.PrettyPrinter()

CONFIG_FILE = 'ow_config.yml'

with open(CONFIG_FILE, 'r') as c:
    config = yaml.load(c, Loader=yaml.CLoader)

weather_url = "https://api.openweathermap.org/data/2.5/weather?q={city}&APPID={token}&units=metric"
pushgateway_url = 'http://localhost:9091/metrics/job/openweather_exporter'

OW_API_TOKEN = config['api_token']
CITY = config['cities'][0]  # for now

if OW_API_TOKEN:
    ## get current weather
    with Rq.urlopen(weather_url.format(city=CITY, token=OW_API_TOKEN)) as f:
        msg = json.loads(f.read())

    ## document computation
    ## elastic_document = {
    #   "location":       msg['coord'],
    ##   "weather_id":     msg['weather'][0]['id'],
    ##   "weather_main":   msg['weather'][0]['main'],
    ##   "weather_descr":  msg['weather'][0]['description'],
    ##   "temp":           msg['main']['temp'],
    ##   "humidity":       msg['main']['humidity'],
    ##   "pressure_sea":   msg['main']['sea_level'] / 1.33322387415,  # hPa->mmHg
    ##   "pressure_gnd":   msg['main']['grnd_level'] / 1.33322387415, # hPa->mmHg
    ##   "wind_speed":     msg['wind']['speed'],
    ##   "wind_deg":       msg['wind']['deg'],
    ##   "clouds":         msg['clouds']['all'],
    #   "rain_1h":        msg.get('rain', {}).get('1h', 0),
    #   "rain_3h":        msg.get('rain', {}).get('3h', 0),
    #   "snow_1h":        msg.get('snow', {}).get('1h', 0),
    #   "show_3h":        msg.get('snow', {}).get('3h', 0),
    #   "timestamp":      msg['dt'],
    ##   "country":        msg['sys']['country'],
    ##   "sunrise":        msg['sys']['sunrise'],
    ##   "sunset":         msg['sys']['sunset'],
    #   "timezone":       msg['timezone'],
    ##   "city_id":        msg['id'],
    ##   "city_name":      msg['name']
    ## }

    city_name = msg['name']
    
    elastic_document = (
    '''# TYPE weather_info gauge\n'''
     f'''weather_info{{location="{city_name}",country="{msg['sys']['country']}",weatherid="{msg['weather'][0]['id']}",weathermain="{msg['weather'][0]['main']}",weatherdesc="{msg['weather'][0]['description']}"}} {msg['id']}\n'''
    '''# TYPE weather_return_code gauge\n'''
    f'''weather_return_code{{name="{city_name}"}} {msg['cod']}\n'''
    '''# TYPE weather_temperature gauge\n'''
    f'''weather_temperature{{name="{city_name}",type="current"}} {msg['main']['temp']}\n'''
    '''# TYPE weather_humidity gauge\n'''
    f'''weather_humidity{{name="{city_name}"}} {msg['main']['humidity']}\n'''
    '''# TYPE weather_pressure gauge\n'''
    f'''weather_pressure{{name="{city_name}",level="ground"}} {msg['main']['grnd_level']}\n'''
    f'''weather_pressure{{name="{city_name}",level="sea"}} {msg['main']['sea_level']}\n'''
    '''# TYPE weather_wind_speed gauge\n'''
    f'''weather_wind_speed{{name="{city_name}"}} {msg['wind']['speed']}\n'''
    '''# TYPE weather_wind_direction gauge\n'''
    f'''weather_wind_direction{{name="{city_name}"}} {msg['wind']['deg']}\n'''
    '''# TYPE weather_clouds_percent gauge\n'''
    f'''weather_clouds_percent{{name="{city_name}"}} {msg['clouds']['all']}\n'''
    '''# TYPE weather_sun_epoch gauge\n'''
    f'''weather_sun_epoch{{name="{city_name}",change="sunrise"}} {msg['sys']['sunrise']}\n'''
    f'''weather_sun_epoch{{name="{city_name}",change="sunset"}} {msg['sys']['sunset']}\n'''
    )

    ## preparing binary data for urllib
    jdata = elastic_document.encode('utf-8')

    ## posting document
    elastic_rq = Rq.Request(pushgateway_url, data=jdata, method='POST')
    elastic_rq.add_header('Content_Type', 'form-data')
    with Rq.urlopen(elastic_rq) as f:
        resp = f.read()

    # pp.pprint(resp)
else:
    # TODO: implement some notification
    print("Couldn't get API token!")
