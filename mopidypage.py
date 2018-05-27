from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from messagepage import MessagePage

class MopidyPage:
    def __init__(self, menu, mopidy):
        self.menu = menu
        self.mopidy = mopidy

        self.pool = ThreadPoolExecutor(5)

    def up(self):
        self.menu.active_index -= 1

    def down(self):
        self.menu.active_index += 1

    def select(self):
        splash_info_page = None
        activeItem = self.menu.items[self.menu.active_index]
        if not activeItem.child_menu is None:
            self.menu = activeItem.child_menu
        elif activeItem.method == "custom.togglepause":
            new_state = self.mopidy.toggle_pause()
            splash_info_page = MessagePage([new_state])
        elif activeItem.method == "core.tracklist.add":
            self.mopidy.tracklist_clear()
            self.mopidy.post(activeItem.method, activeItem.target)
            self.mopidy.play()
        elif activeItem.method == "custom.addplaylist":
            self.mopidy.tracklist_clear()
            f = self.pool.submit(self.mopidy.tracklist_add_playlist, activeItem.target)
            f.add_done_callback(self.mopidy.play)
            splash_info_page = MessagePage(["Adding " + activeItem.text, "Please wait..."])
        else:
            self.mopidy.post(activeItem.method)
        return splash_info_page

    def back(self):
        if not self.menu.parent_menu is None:
            self.menu = self.menu.parent_menu

    def draw_to_screen(self, screen):
        # menu bounds check and scrolling
        if self.menu.active_index >= len(self.menu.items):
            self.menu.active_index = len(self.menu.items) - 1
        elif self.menu.active_index >= self.menu.viewtop_index + screen.height:
            self.menu.viewtop_index = 1 + self.menu.active_index - screen.height
        elif self.menu.active_index < 0:
            self.menu.active_index = 0
        elif self.menu.active_index < self.menu.viewtop_index:
            self.menu.viewtop_index = self.menu.active_index

        screen_row_index = 0
        for i in range(self.menu.viewtop_index, self.menu.viewtop_index + screen.height):
            if i >= len(self.menu.items):
                break
            menuitem = self.menu.items[i]

            left_cursor = right_cursor = ' '
            lineText = menuitem.text[0:screen.width-1]
            if self.menu.active_index == i:
                left_cursor = '['
                right_cursor = ']'
                lineText = menuitem.text[0:screen.width-2]

            #screen.write_line(screen_row_index, 0, '{}{}{}'.format(left_cursor, lineText, right_cursor))
            screen.write_line('{}{}{}'.format(left_cursor, lineText, right_cursor), screen_row_index)
            screen_row_index += 1
