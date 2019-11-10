import json
import pprint
import urllib.request as Rq
from urllib.error import HTTPError

pp = pprint.PrettyPrinter()

INDEX_NAME = 'o_weather_valday'
REPLICAS_NR = 0

index_config = {
    "settings": {
        "index": {
            "number_of_replicas": REPLICAS_NR
        }
    }
}
index_mapping = {
    "properties":
    {
      "location": {
        "type": "geo_point"
      },
      "weather_id": {
        "type": "keyword"
      },
      "weather_main": {
        "type": "keyword"
      },
      "weather_descr": {
        "type": "keyword"
      },
      "temp": {
        "type": "float"
      },
      "humidity": {
        "type": "float"
      },  
      "pressure_sea": {
        "type": "float"
      },
      "pressure_gnd": {
        "type": "float"
      },
      "wind_speed":{
        "type": "float"
      },
      "wind_deg": {
        "type": "short"
      },
      "clouds": {
        "type": "float"
      },
      "rain_1h": {
        "type": "integer"
      },
      "rain_3h": {
        "type": "integer"
      },
      "snow_1h": {
        "type": "integer"
      },
      "show_3h": {
        "type": "integer"
      },
      "timestamp": {
        "type": "date",
        "format": "epoch_second"
      },
      "country": {
        "type": "keyword"
      },
      "sunrise": {
        "type": "date",
        "format": "epoch_second"
      },
      "sunset": {
        "type": "date",
        "format": "epoch_second"
      },
      "timezone": {
        "type": "integer"
      },
      "city_id": {
        "type": "keyword"
      },
      "city_name": {
        "type": "keyword"
      }
    }
  }
create_url = "http://localhost:9200/{index}"
check_url = create_url
map_url = "http://localhost:9200/{index}/_mapping"

# check if index exists
check_rq = Rq.Request(url=check_url.format(index=INDEX_NAME), method='HEAD')
try:
  with Rq.urlopen(check_rq) as f:
    code = f.getcode()
except HTTPError as e:
  code = e.code

# if not, create one
if not code == 200:
  # preparing binary index config data for urllib
  confdata = json.dumps(index_config).encode('utf-8')
  # createting index
  create_rq = Rq.Request(url=create_url.format(index=INDEX_NAME), data=confdata, method='PUT')
  create_rq.add_header('Content-Type', 'application/json; charset=utf-8')
  with Rq.urlopen(create_rq) as f:
    resp = json.loads(f.read())

  # then do mapping
  # preparing binary data mapping data for urllib
  jsondata = json.dumps(index_mapping).encode('utf-8')
  # putting mapping data
  elastic_rq = Rq.Request(map_url.format(index=INDEX_NAME), data=jsondata, method='PUT')
  elastic_rq.add_header('Content-Type', 'application/json; charset=utf-8')
  with Rq.urlopen(elastic_rq) as f:
    resp = json.loads(f.read())

  pp.pprint(resp)
