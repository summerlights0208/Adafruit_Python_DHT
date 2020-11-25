#!/usr/bin/python3
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import requests
import socket
import threading
import logging
import mraa
import RPi.GPIO as GPIO
import http.client as http
import urllib
import json
import time
import Adafruit_DHT

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
deviceId = 'DNVEDCFZ'
deviceKey = '489vJVLK2yn4fXfD' 
# change this to the values from MCS web console
DEVICE_INFO = {
    'device_id' : 'DNVEDCFZ',
    'device_key' : '489vJVLK2yn4fXfD'
}
# change 'INFO' to 'WARNING' to filter info messages
logging.basicConfig(level='INFO')
heartBeatTask = None
def establishCommandChannel():
    # Query command server's IP & port
    connectionAPI = 'https://api.mediatek.com/mcs/v2/devices/%(device_id)s/connections.csv'
    r = requests.get(connectionAPI % DEVICE_INFO,
                 headers = {'deviceKey' : DEVICE_INFO['device_key'],
                            'Content-Type' : 'text/csv'})
    logging.info("Command Channel IP,port=" + r.text)
    (ip, port) = r.text.split(',')

    # Connect to command server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, int(port)))
    s.settimeout(None)

    # Heartbeat for command server to keep the channel alive
    def sendHeartBeat(commandChannel):
        keepAliveMessage = '%(device_id)s,%(device_key)s,0' % DEVICE_INFO
        commandChannel.sendall(keepAliveMessage)
        logging.info("beat:%s" % keepAliveMessage)

    def heartBeat(commandChannel):
        sendHeartBeat(commandChannel)
        # Re-start the timer periodically
        global heartBeatTask
        heartBeatTask = threading.Timer(40, heartBeat, [commandChannel]).start()

    heartBeat(s)
    return s

def waitAndExecuteCommand(commandChannel):
    while True:
        command = commandChannel.recv(1024)
        logging.info("recv:" + command)
        # command can be a response of heart beat or an update of the LED_control,
        # so we split by ',' and drop device id and device key and check length
        fields = command.split(',')[2:]

        if len(fields) > 1:
            timeStamp, dataChannelId, commandString = fields
            if dataChannelId == 'LEDcontrol':
                # check the value - it's either 0 or 1
                commandValue = int(commandString)
                logging.info("led :%d" % commandValue)
                setLED(commandValue)
		
pin = None
def setupLED():
    global pin
    # on LinkIt Smart 7699, pin 44 is the Wi-Fi LED.
    pin = mraa.Gpio(17)
    pin.dir(mraa.DIR_OUT)

def setLED(state):
    # Note the LED is "reversed" to the pin's GPIO status.
    # So we reverse it here.
    if state:
        pin.write(0)
    else:
        pin.write(1)

if __name__ == '__main__':
    setupLED()
    channel = establishCommandChannel()
    waitAndExecuteCommand(channel)




def post_to_mcs(payload): 
	headers = {"Content-type": "application/json", "deviceKey": deviceKey} 
	not_connected = 1 
	while (not_connected):
		try:
			conn = http.HTTPConnection("api.mediatek.com:80")
			conn.connect() 
			not_connected = 0 
		except (http.HTTPException, socket.error) as ex: 
			print ("Error: %s" % ex)
			time.sleep(10)
			 # sleep 10 seconds 
	conn.request("POST", "/mcs/v2/devices/" + deviceId + "/datapoints", json.dumps(payload), headers) 
	response = conn.getresponse() 
	print( response.status, response.reason, json.dumps(payload), time.strftime("%c")) 
	data = response.read() 
	conn.close() 
 


# Parse command line parameters.
sensor_args = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }
if len(sys.argv) == 3 and sys.argv[1] in sensor_args:
    sensor = sensor_args[sys.argv[1]]
    pin = sys.argv[2]
else:
    print('Usage: sudo ./Adafruit_DHT.py [11|22|2302] <GPIO pin number>')
    print('Example: sudo ./Adafruit_DHT.py 2302 4 - Read from an AM2302 connected to GPIO pin #4')
    sys.exit(1)

# Try to grab a sensor reading.  Use the read_retry method which will retry up
# to 15 times to get a sensor reading (waiting 2 seconds between each retry).
humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

# Un-comment the line below to convert the temperature to Fahrenheit.
# temperature = temperature * 9/5.0 + 32

# Note that sometimes you won't get a reading and
# the results will be null (because Linux can't
# guarantee the timing of calls to read the sensor).
# If this happens try again!
if humidity is not None and temperature is not None:
    print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))
else:
    print('Failed to get reading. Try again!')
    sys.exit(1)
while(1):
	h0,t0 = Adafruit_DHT.read_retry(sensor,pin)
	SwitchStatus = GPIO.input(24)
	if h0 is not None and t0 is not None:
		print('Temp={0:0.1f}* Humidity={1:0.1f}%'.format(t0,h0))
		payload = {"datapoints":[{"dataChnId":"Humidity","values":{"value":h0}},{"dataChnId":"Temperature","values":{"value":t0}},{"dataChnId":"SwitchStatus","values":{"value":SwitchStatus}}]} 
		post_to_mcs(payload)
		time.sleep(10)
		if( SwitchStatus == 0):
			print('Button pressed')
		else:
			print('Button released')
	else:
		print('Failed to get reading. Try again!')
		sys.exit(1)

	
	

	
	
	
	
	
	
	
	
	
	
	
	
