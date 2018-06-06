from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import json
from messagepage import MessagePage
from pagemanagercommand import PageManagerCommand
from menu import Menu
from menu import MenuItem

class MopidyPage:
    def __init__(self, mopidy, screen_width):
        self.screen_width = screen_width
        self.mopidy = mopidy
        self.menu = self.arrange_menus()

        self.pool = ThreadPoolExecutor(5)

    def up(self):
        self.menu.active_index -= 1
        return PageManagerCommand.RedrawPage()

    def down(self):
        self.menu.active_index += 1
        return PageManagerCommand.RedrawPage()

    def select(self):
        splash_info_page = None
        activeItem = self.menu.items[self.menu.active_index]

        if activeItem.method == "custom.virtualmenu.listtracksaturi":
            activeItem.child_menu = self.menu_for_tracks_at_uri(activeItem.target)
            self.wire_up_menus(self.menu, True)
            self.menu = activeItem.child_menu
        elif not activeItem.child_menu is None:
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

        if splash_info_page is None:
            return PageManagerCommand.RedrawPage()
        else:
            return PageManagerCommand.SplashPage(splash_info_page)

    def back(self):
        if not self.menu.parent_menu is None:
            self.menu = self.menu.parent_menu
            return PageManagerCommand.RedrawPage()

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

        for screen_row_index, menu_item_index in enumerate(range(self.menu.viewtop_index, self.menu.viewtop_index + screen.height)):
            if menu_item_index >= len(self.menu.items):
                break
            menuitem = self.menu.items[menu_item_index]

            left_cursor = ' '
            right_cursor = ''
            lineText = menuitem.text[0:screen.width-1]
            if self.menu.active_index == menu_item_index:
                left_cursor = '['
                right_cursor = ']'
                lineText = menuitem.text[0:screen.width-2]

            #screen.write_line(screen_row_index, 0, '{}{}{}'.format(left_cursor, lineText, right_cursor))
            screen.write_line('{}{}{}'.format(left_cursor, lineText, right_cursor), screen_row_index)

    def arrange_menus(self):
        menuitem_radmac = MenuItem("RadMac", "custom.virtualmenu.listtracksaturi", "file:///media/data/get-iplayer-downloads")
        # Dummy menu so that >> gets displayed
        menuitem_radmac.child_menu = Menu([])

        menuitem_radio = MenuItem("Radio")
        menuitem_radio.child_menu = Menu([
            menuitem_radmac,
            MenuItem("Classic FM", "core.tracklist.add", "tunein:station:s8439"),
            MenuItem("BBC Radio 2", "core.tracklist.add", "tunein:station:s24940"),
            MenuItem("BBC Radio 3", "core.tracklist.add", "tunein:station:s24941"),
            MenuItem("BBC Radio 4", "core.tracklist.add", "tunein:station:s25419"),
            MenuItem("BBC Radio 6", "core.tracklist.add", "tunein:station:s44491"),        
            MenuItem("BBC Sussex", "core.tracklist.add", "tunein:station:s46590"),
            MenuItem("Eagle Radio", "core.tracklist.add", "tunein:station:s45515")
        ])

        menuitem_playlists = MenuItem("Playlists")
        menuitem_playlists.child_menu = self.menu_for_playlists()

        menu = Menu([
                    menuitem_radio,
                    MenuItem("Play/Pause", "custom.togglepause"),
                    menuitem_playlists,
                    MenuItem("Artists")
        ])

        self.wire_up_menus(menu)
        return menu

    def wire_up_menus(self, menu, preserve_active_items=False):
        first_item = True
        for menu_item in menu.items:
            if first_item and not preserve_active_items:
                menu_item.active = True
                first_item = False
            if not menu_item.child_menu is None:
                menu_item.text = menu_item.text.ljust(self.screen_width - 5) + ">>"
                menu_item.child_menu.parent_menu = menu
                self.wire_up_menus(menu_item.child_menu, preserve_active_items)
            menu_item.text = menu_item.text.ljust(self.screen_width)

    def menu_for_tracks_at_uri(self, mopidy_folder_uri):
        response = self.mopidy.post("core.library.browse", mopidy_folder_uri)
        response_json = json.loads(response)
        sorted_response_json = reversed(sorted(response_json["result"], key=lambda x: x["name"]))
        menu_items = list(map(
            lambda i: MenuItem(
                i["name"][12:].replace("_"," ").replace(".m4a",""),
                "core.tracklist.add",
                i["uri"]),
            sorted_response_json))

        menu_items = [elem for elem in menu_items if elem.target.endswith(".m4a")] 

        return Menu(menu_items)

    def menu_for_playlists(self):
        response = self.mopidy.post("core.playlists.get_playlists")
        response_json = json.loads(response)
        sorted_response_json = sorted(response_json["result"], key=lambda x: x["name"])
        menu_items = list(map(
            lambda i: MenuItem(
                i["name"],
                "custom.addplaylist",
                i["uri"]),
            sorted_response_json))

        return Menu(menu_items)
