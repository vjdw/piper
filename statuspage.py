from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from pagemanagercommand import PageManagerCommand
from messagepage import MessagePage
from websocket import create_connection

class StatusPage:
    def __init__(self):
        self.pool = ThreadPoolExecutor(5)
        self.web_socket_url = "ws://hunchcorn.local:6680/mopidy/ws" 
        self.ws = create_connection(self.web_socket_url)

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
        screen.write_line('status page', 0)
