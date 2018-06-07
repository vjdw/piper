from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from pagemanagercommand import PageManagerCommand
from messagepage import MessagePage
from websocket import create_connection
import urllib.request
import json
from threading import Timer

class StatusPage:
    def __init__(self, screen):
        self.screen = screen # raise draw event instead of keeping screen?
        self.pool = ThreadPoolExecutor(5)
        self.web_socket_url = "ws://hunchcorn.local:6680/mopidy/ws" 
        self.ws = create_connection(self.web_socket_url)

        self.update_weather_timer = None
        self.run_update_weather_timer()

    def up(self):
        return PageManagerCommand.ClosePage()

        #result =  self.ws.recv()
        #result = result[:16]
        #return PageManagerCommand.SplashPage(MessagePage([result]))

    def down(self):
        return PageManagerCommand.ClosePage()

    def select(self):
        return PageManagerCommand.ClosePage()

    def back(self):
        return PageManagerCommand.ClosePage()

    def draw_to_screen(self, screen):
        screen.clear()
        screen.write_line(self.weather_1, 0)
        screen.write_line(self.weather_2, 1)
        screen.write_line(self.weather_3, 2)

    def run_update_weather_timer(self):
        if self.update_weather():
            getAgainSeconds = 600
        else:
            getAgainSeconds = 20
        
        if not self.update_weather_timer is None:
            self.update_weather_timer.cancel()
        self.update_weather_timer = Timer(getAgainSeconds, self.run_update_weather_timer)
        self.update_weather_timer.start()

    def update_weather(self):
        isSuccess = True
        try:
            req = urllib.request.Request("https://api.openweathermap.org/data/2.5/weather?id=2638580&APPID=e01f62f6a7b1053f6658e9242a61bff4")
            response = urllib.request.urlopen(req)
            json_response = json.loads(response.read().decode('utf-8'))
            temp = round((json_response["main"]["temp"] - 273.15))
            temp_min = round((json_response["main"]["temp_min"] - 273.15))
            temp_max = round((json_response["main"]["temp_max"] - 273.15))
            description = json_response["weather"][0]["description"]
            pressure = json_response["main"]["pressure"]
            humidity = json_response["main"]["humidity"]
            # The HD44780 has two character code pages. The A01 is the default, and includes a characters that looks like a degree symbol.
            # The ß character has the same ASCII value but in the A02 code page, and so gets displayed as a degree symbol.
            self.weather_1 = "{}ßC P:{}mb H:{}%".format(temp, pressure, humidity)
            self.weather_2 = description
            self.weather_3 = "min:{}ßC max:{}ßC".format(temp_min, temp_max)
        except Exception as err:
            isSuccess = False
            self.weather_1 = "weather error"
            self.weather_2 = err
            self.weather_3 = ""

        self.draw_to_screen(self.screen)
        return isSuccess