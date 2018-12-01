import os
import time
import ConfigParser
import json
import requests
import uuid

class BingSTT(object):
    TOKEN_URI = 'https://westus.api.cognitive.microsoft.com/sts/v1.0/issueToken'
    TOKEN_VALIDITY = 10 * 60 - 10 # 10min -10s to have a token valid during the query

    API_URI = 'https://westus.stt.speech.microsoft.com/speech/recognition/interactive/cognitiveservices/v1'
    API_SUCCESS = 'Success'
    
    def __init__(self):
        self.api_key = None
        self._read_config()
        self.token = None
        self.token_date = 0.0

    def _read_config(self):
        config = ConfigParser.RawConfigParser()
        config.read('config.ini')

        self.api_key = config.get('bing', 'api_key')
        

    def _assert_token(self):        
        now = time.time()
        if now < self.token_date + self.TOKEN_VALIDITY:  # token is still valid, use it
            return
            
        # ok ask for a new token
        headers = {'Content-Type' : 'application/x-www-form-urlencoded',
                   'Content-Length' : '0',
                   'Ocp-Apim-Subscription-Key': self.api_key}
        payload = {'grant_type':'client_credentials',
                   'scope':'https://speech.platform.bing.com'
                   }
        uri = self.TOKEN_URI
        data = json.dumps(payload)
        print('URI: %s  data=%s   headers=%s' % (uri, data, headers))
        r = requests.post(uri, data=data, headers=headers)
        self.token = r.content
        self.token_date = now
        
        
        

    def parse_sound(self, sound_file):
        if not os.path.exists(sound_file):
            print('ERROR: the file %s does not exists' % sound_file)
            return None
        self._assert_token()


        endpoint = 'https://speech.platform.bing.com/recognize'
        request_id = uuid.uuid4()
        # Params form Microsoft Example
        params = {#'scenarios': 'ulm',
            #'appid': 'D4D52672-91D7-4C74-8AD8-42B1D98141A5',
                  'locale': 'fr-FR',
            'language' :'fr-FR',
             #     'version': '3.0',
                  'format': 'json',
              #    'instanceid': '565D69FF-E928-4B7E-87DA-9A750B96D9E3',
               #   'requestid': request_id,
                #  'device.os': 'linux'
        }
        content_type = "audio/wav; codec=""audio/pcm""; samplerate=16000"
        
        def stream_audio_file(speech_file, chunk_size=1024):
            with open(speech_file, 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    yield data
                    
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Content-Type': content_type}
        resp = requests.post(self.API_URI,
                             params=params,
                             data=stream_audio_file(sound_file),
                             headers=headers)
        raw_return = resp.text
        print('Raw return: %s' % raw_return)
        j = json.loads(raw_return)
        status = j['RecognitionStatus']
        text = j['DisplayText']
        if status != self.API_SUCCESS:
            print('ERROR: cannot match the sound')
            return None
        print('Match: %s' % text)


if __name__ == '__main__':
    engine = BingSTT()
    engine.parse_sound('/dev/shm/coucou.wav')


# Pour enregister un son: 
# AUDIODEV=hw:1,0 rec coucou.wav
    
