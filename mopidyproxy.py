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
        #responseObj = json2obj(response_json)playlist_track_uris
        #return response_json

    def play(self, *args):
        return self.post("core.playback.play")

    def toggle_pause(self):
        response = self.post("core.playback.get_state")
        response_json = json.loads(response)
        if response_json["result"] == "playing":
            return self.post("core.playback.pause")
        else:
            return self.post("core.playback.play")

    def tracklist_clear(self):
        return self.post("core.tracklist.clear")

    def tracklist_add(self, trackUri):
        return self.post("core.tracklist.add", trackUri)

    def tracklist_add_playlist(self, playlistUri):
        response = self.post("core.playlists.lookup", playlistUri)
        response_json = json.loads(response)

        playlist_track_uris = list(map(
            lambda i: i["uri"],
            response_json["result"]["tracks"]))
        playlist_track_uris_json = json.dumps(playlist_track_uris)

        req = urllib.request.Request(self.endpoint)
        req.add_header('Content-Type', 'application/json; charset=utf-8')

        paramsJson = ""
        paramsJson = ", \"params\":{{\"uris\":{0}}}".format(playlist_track_uris_json)
        jsondata = "{{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"{0}\"{1}}}".format("core.tracklist.add", paramsJson)
        
        jsondataasbytes = jsondata.encode('utf-8')
        #self.logger.write(jsondata)
        req.add_header('Content-Length', len(jsondataasbytes))
        response = urllib.request.urlopen(req, jsondataasbytes)
        return response.read().decode('utf-8')
