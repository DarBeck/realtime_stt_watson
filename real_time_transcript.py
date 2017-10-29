# Copyright 2017 Darren Beckford All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Real time text-to-speech service using the Watson Cloud Services
# Email: darren.beckford@futuretechja.com
# Special thanks to the Watson and Bluemix community

import asyncio
import websockets
import json
import requests
import pyaudio
import time

# Variables to use for recording audio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 16000

p = pyaudio.PyAudio()

# This is the language model to use to transcribe the audio
model = "en-US_BroadbandModel"

# These are the urls we will be using to communicate with Watson
default_url = "https://stream.watsonplatform.net/speech-to-text/api"
token_url = "https://stream.watsonplatform.net/authorization/api/v1/token?" \
            "url=https://stream.watsonplatform.net/speech-to-text/api"
url = "wss://stream.watsonplatform.net/speech-to-text/api/v1/recognize?model=en-US_BroadbandModel"

# BlueMix app credentials
username = ""   # Your Bluemix App username
password = ""   # Your Bluemix App password

# Send a request to get an authorization key
r = requests.get(token_url, auth=(username, password))
auth_token = r.text
token_header = {"X-Watson-Authorization-Token": auth_token}

# Params to use for Watson API
params = {
    "word_confidence": True,
    "content_type": "audio/l16;rate=16000;channels=2",
    "action": "start",
    "interim_results": True
}

# Opens the stream to start recording from the default microphone
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK)


async def send_audio(ws):
    # Starts recording of microphone
    print("* READY *")

    start = time.time()
    while True:
        try:
            print(".")
            data = stream.read(CHUNK)
            await ws.send(data)
            if time.time() - start > 20:
                await ws.send(json.dumps({'action': 'stop'}))
                return False
        except Exception as e:
            print(e)
            return False

    # Stop the stream and terminate the recording
    stream.stop_stream()
    stream.close()
    p.terminate()


async def speech_to_text():
    async with websockets.connect(url, extra_headers=token_header) as conn:
        # Send request to watson and waits for the listening response
        send = await conn.send(json.dumps(params))
        rec = await conn.recv()
        print(rec)
        asyncio.ensure_future(send_audio(conn))

        # Keeps receiving transcript until we have the final transcript
        while True:
            try:
                rec = await conn.recv()
                parsed = json.loads(rec)
                transcript = parsed["results"][0]["alternatives"][0]["transcript"]
                print(transcript)
                #print(parsed)
                if "results" in parsed:
                    if len(parsed["results"]) > 0:
                        if "final" in parsed["results"][0]:
                            if parsed["results"][0]["final"]:
                                #conn.close()
                                #return False
                                pass
            except KeyError:
                conn.close()
                return False

# Starts the application loop
loop = asyncio.get_event_loop()
loop.run_until_complete(speech_to_text())
loop.close()
