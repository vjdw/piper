from concurrent.futures import ThreadPoolExecutor, wait, as_completed

class PageManager:
    def __init__(self, screen, main_menu, mopidy):
        self.screen = screen
        self.main_menu = main_menu
        self.mopidy = mopidy
        self.pool = ThreadPoolExecutor(5)

    def up(self):
        self.main_menu.active_index -= 1

    def down(self):
        self.main_menu.active_index += 1

    def select(self):
        activeItem = self.main_menu.items[self.main_menu.active_index]
        if not activeItem.child_menu is None:
            self.main_menu = activeItem.child_menu
            self.screen.clear()
        elif activeItem.method == "custom.togglepause":
            self.mopidy.toggle_pause()
        elif activeItem.method == "core.tracklist.add":
            self.mopidy.tracklist_clear()
            self.mopidy.post(activeItem.method, activeItem.target)
            self.mopidy.play()
        elif activeItem.method == "custom.addplaylist":
            self.mopidy.tracklist_clear()
            f = self.pool.submit(self.mopidy.tracklist_add_playlist, activeItem.target)
            f.add_done_callback(self.mopidy.play)
        else:
            self.mopidy.post(activeItem.method)

    def back(self):
        if not self.main_menu.parent_menu is None:
            self.main_menu = self.main_menu.parent_menu
            self.screen.clear()

    def draw_menu_to_screen(self):
        # menu bounds check and scrolling
        if self.main_menu.active_index >= len(self.main_menu.items):
            self.main_menu.active_index = len(self.main_menu.items) - 1
        elif self.main_menu.active_index >= self.main_menu.viewtop_index + self.screen.height:
            self.main_menu.viewtop_index = 1 + self.main_menu.active_index - self.screen.height
        elif self.main_menu.active_index < 0:
            self.main_menu.active_index = 0
        elif self.main_menu.active_index < self.main_menu.viewtop_index:
            self.main_menu.viewtop_index = self.main_menu.active_index

        screen_row_index = 0
        for i in range(self.main_menu.viewtop_index, self.main_menu.viewtop_index + self.screen.height):
            if i >= len(self.main_menu.items):
                break
            menuitem = self.main_menu.items[i]

            left_cursor = ' '
            right_cursor = ''
            lineText = menuitem.text[0:self.screen.width-2]
            if self.main_menu.active_index == i:
                left_cursor = '['
                right_cursor = ']'
                lineText = menuitem.text[0:self.screen.width-3]
            self.screen.write_line(screen_row_index, 0, '{}{}{}'.format(left_cursor, lineText, right_cursor))

            screen_row_index += 1

        self.screen.refresh()
