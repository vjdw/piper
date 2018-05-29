from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from curses import wrapper
import time
import threading
from screen import Screen

class PageManager:
    def __init__(self, screen, main_page):
        self.screen = screen
        self.page_stack = [main_page]
        self.pool = ThreadPoolExecutor(5)
        self.stop_running = False

        self.lock = threading.Lock()

    def get_top_page(self):
        return self.page_stack[-1]

    top_page = property(get_top_page)

    def run(self):
        with self.lock:
            self.draw()
        while not self.stop_running:
            #self.draw()
            time.sleep(1.1)

    def stop(self):
        self.stop_running = True

    def up(self):
        with self.lock:
            self.top_page.up()
            self.draw()

    def down(self):
        with self.lock:
            self.top_page.down()
            self.draw()

    def select(self):
        with self.lock:
            splash_info_page = self.top_page.select()
            if not splash_info_page is None:
                self.page_stack.append(splash_info_page)
                self.draw()
                time.sleep(3.5)
                self.page_stack.pop()
            self.draw()

    def back(self):
        with self.lock:
            self.top_page.back()
            self.draw()

    def draw(self):
        self.top_page.draw_to_screen(self.screen)
