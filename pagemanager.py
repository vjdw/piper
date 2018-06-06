from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from curses import wrapper
import time
import threading
from threading import Timer
from screen import Screen
from statuspage import StatusPage
from pagemanagercommand import PageManagerCommand

class PageManager:
    def __init__(self, screen, main_page):
        self.screen = screen
        self.page_stack = [main_page]
        self.page_stack_lock = threading.RLock()
        self.pool = ThreadPoolExecutor(5)
        self.stop_running = False

        self.idle_timer = None

    def get_top_page(self):
        return self.page_stack[-1]

    top_page = property(get_top_page)

    def run(self):
        self.reset_idle_timer()
        with self.page_stack_lock:
            self.draw()
        while not self.stop_running:
            #self.draw()
            time.sleep(1.1)

    def stop(self):
        self.stop_running = True

    def up(self):
        self.reset_idle_timer()
        with self.page_stack_lock:
            page_command = self.top_page.up()
            self.process_page_command(page_command)

    def down(self):
        self.reset_idle_timer()
        with self.page_stack_lock:
            page_command = self.top_page.down()
            self.process_page_command(page_command)

    def select(self):
        self.reset_idle_timer()
        with self.page_stack_lock:
            page_command = self.top_page.select()
            self.process_page_command(page_command)

    def back(self):
        self.reset_idle_timer()
        with self.page_stack_lock:
            page_command = self.top_page.back()
            self.process_page_command(page_command)

    def process_page_command(self, page_command):
        with self.page_stack_lock:
            if page_command is None:
                return
            elif page_command.cmd == PageManagerCommand.redraw_command:
                self.draw()
            elif page_command.cmd == PageManagerCommand.displaypage_command:
                self.page_stack.append(page_command.arg)
                self.draw()
            elif page_command.cmd == PageManagerCommand.splashpage_command:
                self.page_stack.append(page_command.arg)
                self.draw()
                time.sleep(3)
                self.page_stack.pop()
                self.draw()
            elif page_command.cmd == PageManagerCommand.close_command:
                self.page_stack.pop()
                self.draw()

    def draw(self):
        with self.page_stack_lock:
            self.top_page.draw_to_screen(self.screen)

    def display_idle_page(self):
        self.process_page_command(PageManagerCommand.DisplayPage(StatusPage()))

    def reset_idle_timer(self):
        if not self.idle_timer is None:
            self.idle_timer.cancel()
        self.idle_timer = Timer(10, self.display_idle_page)
        self.idle_timer.start()
