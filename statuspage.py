from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from pagemanagercommand import PageManagerCommand
from messagepage import MessagePage
from websocket import create_connection
import urllib.request
import json
from threading import Timer
import time
import requests

class StatusPage:
    def __init__(self, screen, mopidy):
        self.screen = screen # raise draw event instead of keeping screen?
        self.mopidy = mopidy
        #self.pool = ThreadPoolExecutor(5)
        #self.web_socket_url = "ws://hunchcorn:6680/mopidy/ws" 
        #self.ws = create_connection(self.web_socket_url)
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

    def togglepause(self):
        self.mopidy.toggle_pause()

    def draw_to_screen(self, screen):
        screen.clear()
        screen.write_line(self.weather_1, 0)
        screen.write_line(self.weather_2, 1)
        screen.write_line(self.weather_3, 2)
        screen.write_line(self.weather_4, 3)

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
        cityId = "2638580"
        apiKey = "e01f62f6a7b1053f6658e9242a61bff4"
        isSuccess = True
        try:
            req = urllib.request.Request("https://api.openweathermap.org/data/2.5/weather?id={}&APPID={}".format(cityId, apiKey))
            response = urllib.request.urlopen(req)
            json_response = json.loads(response.read().decode('utf-8'))
            now_temp = self.to_celsius(json_response["main"]["temp"])
            description = json_response["weather"][0]["description"]
            pressure = json_response["main"]["pressure"]
            humidity = json_response["main"]["humidity"]
            # The HD44780 has two character code pages. The A01 is the default, and includes a characters that looks like a degree symbol.
            # The ß character has the same ASCII value but in the A02 code page, and so gets displayed as a degree symbol.
            self.weather_1 = "{}ßC P:{}mb H:{}%".format(now_temp, pressure, humidity)
            self.weather_2 = description
        except Exception as inst:
            print("inst")
            isSuccess = False
            self.weather_1 = "weather error"
            self.weather_2 = ""

        try:
            forecastUrl = 'https://api.openweathermap.org/data/2.5/forecast?id={}&APPID={}'.format(cityId, apiKey)
            forecastResponse = requests.get(url=forecastUrl)
            today = time.localtime().tm_yday
            tomorrow = today + 1
            
            # wrap round 365/366 days
            if(tomorrow == 367 and year%4==0 and (year%100!=0 or year%400==0)):
                tomorrow = 1
            elif tomorrow == 366:
                tomorrow = 1
            
            today_temp_max = -999
            today_temp_min = 999
            today_rain_mm = {0:-1,1:-1,2:-1,3:-1,4:-1,5:-1,6:-1,7:-1}
            tomorrow_temp_max = -999
            tomorrow_temp_min = 999
            tomorrow_rain_mm = {0:-1,1:-1,2:-1,3:-1,4:-1,5:-1,6:-1,7:-1}
            
            for forecast in forecastResponse.json().get('list'):
                forecast_time = time.gmtime(int(forecast['dt']))
                forecast_threehourly_index = forecast_time.tm_hour / 3
                forecast_temp = self.to_celsius(forecast['main']['temp'])

                if forecast_time.tm_yday == today:
                    if today_temp_max < forecast_temp:
                        today_temp_max = forecast_temp
                    if today_temp_min > forecast_temp:
                        today_temp_min = forecast_temp
                    if 'rain' in forecast and '3h' in forecast['rain']:
                        today_rain_mm[forecast_threehourly_index] = forecast['rain']['3h']
                    else:
                        today_rain_mm[forecast_threehourly_index] = 0
                elif forecast_time.tm_yday == tomorrow:
                    if tomorrow_temp_max < forecast_temp:
                        tomorrow_temp_max = forecast_temp
                    if tomorrow_temp_min > forecast_temp:
                        tomorrow_temp_min = forecast_temp
                    if 'rain' in forecast and '3h' in forecast['rain']:
                        tomorrow_rain_mm[forecast_threehourly_index] = forecast['rain']['3h']
                    else:
                        tomorrow_rain_mm[forecast_threehourly_index] = 0

            if now_temp > today_temp_max:
                today_temp_max = now_temp
            if now_temp < today_temp_min:
                today_temp_min = now_temp

            # (These values multiplied by 3 because forecast is in 3 hour blocks)
            # Very light rain 	precipitation rate is < 0.25 mm/hour
            # Light rain    	precipitation rate is between 0.25mm/hour and 1.0mm/hour
            # Moderate rain 	precipitation rate is between 1.0 mm/hour and 4.0 mm/hour
            # Heavy rain    	precipitation rate is between 4.0 mm/hour and 16.0 mm/hour
            # Very heavy rain   precipitation rate is between 16.0 mm/hour and 50 mm/hour
            # Extreme rain 	    precipitation rate is > 50.0 mm/hour 
            bar_char_lookup = {48:"\x07",24:"\x06",12:"\x05",6:"\x04",3:"\x03",1.5:"\x02",0.75:"\x01",0:"\x00",-1:" ",-2:"¥"}
            today_rain_text = ""
            for key in today_rain_mm:
                for threshold in reversed(sorted(bar_char_lookup)):
                    if today_rain_mm[key] > threshold:
                        today_rain_text += bar_char_lookup[threshold]
                        break
            tomorrow_rain_text = ""
            for key in tomorrow_rain_mm:
                for threshold in reversed(sorted(bar_char_lookup)):
                    if tomorrow_rain_mm[key] > threshold:
                        tomorrow_rain_text += bar_char_lookup[threshold]
                        break

            self.weather_3 = "2D:{}/{}ßC {}".format(today_temp_min, today_temp_max, today_rain_text)
            self.weather_4 = "2M:{}/{}ßC {}".format(tomorrow_temp_min, tomorrow_temp_max, tomorrow_rain_text)
        except:
            self.weather_3 = "forecast error"
            self.weather_4 = ""
            isSuccess = False

        try:
            self.draw_to_screen(self.screen)
        except:
            self.weather_1 = "screen error"
            self.weather_2 = ""
            self.weather_3 = ""
            self.weather_4 = ""
            isSuccess = False

        return isSuccess

    def to_celsius(self, kelvin):
        return round(kelvin - 273.15)
