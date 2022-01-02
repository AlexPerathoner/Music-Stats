from subprocess import Popen, PIPE
from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate an API token from the "API Tokens Tab" in the UI
token = "m3_qTJNHan6NP0jFkdkLjFUdtNy5cCnFnQpWQVfDDUXQtmMf8o-udOP8t9yxPDKQHkvKqPtvJpKLdO-FaoG4mQ=="
org = "AlexPera"
bucket = "MusicLibrary"
currTime = datetime.utcnow() #.today()

with InfluxDBClient(url="http://localhost:8086", token=token, org=org) as client:
    write_api = client.write_api(write_options=SYNCHRONOUS)

    point = Point("Black Coffee") \
        .tag("artist", "Wolfgang Lohr & Louie Prima") \
        .tag("album", "") \
        .field("playCount", 35) \
        .time(currTime, WritePrecision.NS)
    
    write_api.write(bucket, org, point)


    point = Point("Black Coffee") \
        .tag("artist", "PiSk") \
        .tag("album", "Black Coffee") \
        .field("playCount", 40) \
        .time(currTime, WritePrecision.NS)
    
    write_api.write(bucket, org, point)