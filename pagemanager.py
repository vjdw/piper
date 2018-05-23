from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from curses import wrapper
import time
from screen import Screen

class PageManager:
    def __init__(self, screen, page_stack):
        self.screen = screen
        self.page_stack = page_stack
        self.pool = ThreadPoolExecutor(5)
        self.stop_running = False

    def get_top_page(self):
        return self.page_stack[-1]

    top_page = property(get_top_page)

    def run(self):
        while not self.stop_running:
            self.draw()
            time.sleep(0.1)

    def stop(self):
        self.stop_running = True

    def up(self):
        self.top_page.up()

    def down(self):
        self.top_page.down()

    def select(self):
        splash_info_page = self.top_page.select()
        if not splash_info_page is None:
            self.page_stack.append(splash_info_page)
            time.sleep(1)
            self.page_stack.pop()

    def back(self):
        self.top_page.back()

    def draw(self):
        self.top_page.draw_to_screen(self.screen)
        self.screen.refresh()
