import urllib.request
import json

class MopidyProxy:
    def __init__(self, logger, endpoint):
        self.logger = logger
        self.endpoint = endpoint

    def post(self, method, trackUri=None):
        req = urllib.request.Request(self.endpoint)
        req.add_header('Content-Type', 'application/json; charset=utf-8')

        paramsJson = ""
        if not trackUri is None:
            paramsJson = ", \"params\":{{\"uri\":\"{0}\"}}".format(trackUri)
        jsondata = "{{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"{0}\"{1}}}".format(method, paramsJson)
        
        jsondataasbytes = jsondata.encode('utf-8')
        self.logger.write(jsondata)
        req.add_header('Content-Length', len(jsondataasbytes))
        response = urllib.request.urlopen(req, jsondataasbytes)
        return response.read().decode('utf-8')
        #responseObj = json2obj(responseJson)
        #return responseJson

    def play(self):
        return self.post("core.playback.play")

    def toggle_pause(self):
        response = self.post("core.playback.get_state")
        responseJson = json.loads(response)
        if responseJson["result"] == "playing":
            return self.post("core.playback.pause")
        else:
            return self.post("core.playback.play")

    def tracklist_add(self, trackUri):
        return self.post("core.tracklist.add", trackUri)
