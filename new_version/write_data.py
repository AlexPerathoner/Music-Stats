from subprocess import Popen, PIPE
from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate an API token from the "API Tokens Tab" in the UI
token = "m3_qTJNHan6NP0jFkdkLjFUdtNy5cCnFnQpWQVfDDUXQtmMf8o-udOP8t9yxPDKQHkvKqPtvJpKLdO-FaoG4mQ=="
org = "AlexPera"
bucket = "MusicLibrary"
currTime = datetime.utcnow() #.today()

text_file = open("outputAppleScript.txt", encoding='utf-16')
fileData = text_file.read()
text_file.close()


list = fileData.split(";")[:-1]
if(len(list) % 2 != 0):
    script = 'display notification "List is not even!" with title "Error in Music Library Script!"'
    p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(script)
    exit(-1)

with InfluxDBClient(url="http://localhost:8086", token=token, org=org) as client:
    write_api = client.write_api(write_options=SYNCHRONOUS)

    for i in range(0, len(list), 4):
        name = list[i]
        artist = list[i+1] 
        album = list[i+2]
        count = int(list[i+3])
        print("Adding " + name + " by " + artist + " (" + str(count) + ")")
        if(type(count) != int):
            script = 'display notification "Some numbers are wrong!" with title "Error in Music Library Script!"'
            p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            stdout, stderr = p.communicate(script)
            exit(-1)

        point = Point(name) \
            .field("playCount", count) \
            .tag("artist", artist) \
            .tag("album", album) \
            .time(currTime, WritePrecision.NS)
        
        write_api.write(bucket, org, point)