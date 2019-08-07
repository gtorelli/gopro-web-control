import sys
import socket
import webbrowser
import os

try:

    from urllib.request import urlopen
except ImportError:

    from urllib2 import urlopen
import subprocess
from time import sleep
import signal
import json
import re
import http


def get_command_msg(id):
    return "_GPHD_:%u:%u:%d:%1lf\n" % (0, 0, 2, 0)


VERBOSE = False
RECORD = False
SAVE = False
SAVE_FILENAME = "goprofeed3"
SAVE_FORMAT = "ts"
SAVE_LOCATION = "/tmp/"
# Abrir html
url = "file:///.index.html"
webbrowser.open(url, new=2)


def gopro_live():
    UDP_IP = "10.5.5.9"
    UDP_PORT = 8554
    KEEP_ALIVE_PERIOD = 2500
    KEEP_ALIVE_CMD = 2

    MESSAGE = get_command_msg(KEEP_ALIVE_CMD)
    URL = "http://10.5.5.9:8080/live/amba.m3u8"
    try:
        # original code - response_raw = urllib.request.urlopen('http://10.5.5.9/gp/gpControl').read().decode('utf-8')
        response_raw = urlopen(
            'http://10.5.5.9/gp/gpControl').read().decode('utf-8')
        jsondata = json.loads(response_raw)
        response = jsondata["info"]["firmware_version"]
    except http.client.BadStatusLine:
        response = urlopen('http://10.5.5.9/camera/cv').read().decode('utf-8')
    if "HD4" in response or "HD3.2" in response or "HD5" in response or "HX" in response or "HD6" in response:
        print("branch HD4")
        print(jsondata["info"]["model_name"] + "\n" +
              jsondata["info"]["firmware_version"])
        ##
        # HTTP GETs the URL that tells the GoPro to start streaming.
        ##
        urlopen(
            "http://10.5.5.9/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart").read()
        if RECORD:
            urlopen("http://10.5.5.9/gp/gpControl/command/shutter?p=1").read()
        print("UDP target IP:", UDP_IP)
        print("UDP target port:", UDP_PORT)
        print("message:", MESSAGE)
        print("Recording on camera: " + str(RECORD))

        loglevel_verbose = ""
        if VERBOSE == False:
            loglevel_verbose = "-loglevel panic"
        if SAVE == False:
            subprocess.Popen("ffplay " + loglevel_verbose +
                             " -fflags nobuffer -f:v mpegts -probesize 8192 udp://10.5.5.100:8554", shell=True)
        else:
            if SAVE_FORMAT == "ts":
                TS_PARAMS = " -acodec copy -vcodec copy "
            else:
                TS_PARAMS = ""
            SAVELOCATION = SAVE_LOCATION + SAVE_FILENAME + "." + SAVE_FORMAT
            print("Recording locally: " + str(SAVE))
            print("Recording stored in: " + SAVELOCATION)
            print("Note: Preview is not available when saving the stream.")
            subprocess.Popen(
                "ffmpeg -i 'udp://:10.5.5.100:8554' -fflags nobuffer -f:v mpegts -probesize 8192 " + TS_PARAMS + SAVELOCATION, shell=True)
        if sys.version_info.major >= 3:
            MESSAGE = bytes(MESSAGE, "utf-8")
        print("Press ctrl+C to quit this application.\n")
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
            sleep(KEEP_ALIVE_PERIOD / 1000)
    else:
        print("branch hero3" + response)
        if "Hero3" in response or "HERO3+" in response:
            print("branch hero3")
            PASSWORD = urlopen("http://10.5.5.9/bacpac/sd").read()
            print("HERO3/3+/2 camera")
            Password = str(PASSWORD, 'utf-8')
            text = re.sub(r'\W+', '', Password)
            urlopen("http://10.5.5.9/camera/PV?t=" + text + "&p=%02")
            subprocess.Popen("ffplay " + URL, shell=True)


def quit_gopro(signal, frame):
    if RECORD:
        urlopen("http://10.5.5.9/gp/gpControl/command/shutter?p=0").read()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, quit_gopro)
    gopro_live()
