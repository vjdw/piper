import curses

class Screen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cursor_x = 0
        self.cursor_y = 0
        curses.initscr()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.curs_set(0)
        self.win = curses.newwin(self.height, self.width, self.cursor_y, self.cursor_x)
        self.win.bkgd(' ', curses.color_pair(1))
        self.win.clear()

    def write_line(self, x, y, text):
        self.win.addstr(x, y, text)
        
    def refresh(self):
        self.win.refresh()

    def clear(self):
        self.win.clear()

    def get_char(self):
        return self.win.getch()
