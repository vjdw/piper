#!/usr/bin/env python3

from curses import wrapper
import json
from collections import namedtuple

from logger import Logger
from screen import Screen
from menu import Menu
from menu import MenuItem
from mopidyproxy import MopidyProxy    

def draw_menu_to_screen(screen, menu):
    screen_row_index = 0
    for i in range(menu.viewtop_index, menu.viewtop_index + screen.height):
        if i >= len(menu.items):
            break
        menuitem = menu.items[i]

        left_cursor = ' '
        right_cursor = ''
        lineText = menuitem.text[0:screen.width-2]
        if menu.active_index == i:
            left_cursor = '['
            right_cursor = ']'
            lineText = menuitem.text[0:screen.width-3]
        screen.write_line(screen_row_index, 0, '{}{}{}'.format(left_cursor, lineText, right_cursor))

        screen_row_index += 1

    screen.refresh()

def arrange_menus(mopidy):
    menuitem_radmac = MenuItem("RadMac", "", "", True)
    menuitem_radmac.child_menu = menu_for_tracks_at_uri(mopidy, "file:///media/data/get-iplayer-downloads")

    menuitem_radio = MenuItem("Radio", "", "", True)
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

    return Menu([
                menuitem_radio,
                MenuItem("Play/Pause", "custom.togglepause"),
                MenuItem("Playlists", "core.tracklist.add"),
                MenuItem("Artists")
    ])

def wire_up_menus(menu, lcd):
    for menu_item in menu.items:
        if not menu_item.child_menu is None:
            menu_item.text = menu_item.text.ljust(lcd.width - 5) + ">>"
            menu_item.child_menu.parent_menu = menu
            wire_up_menus(menu_item.child_menu, lcd)
        menu_item.text = menu_item.text.ljust(lcd.width)

def menu_for_tracks_at_uri(mopidy, mopidy_folder_uri):
    response = mopidy.post("core.library.browse", mopidy_folder_uri)
    responseJson = json.loads(response)
    sortedResponseJson = reversed(sorted(responseJson["result"], key=lambda x: x["name"]))
    menuItems = list(map(
        lambda i: MenuItem(
            i["name"][12:].replace("_"," ").replace(".m4a",""),
            "core.tracklist.add",
            i["uri"]),
        sortedResponseJson))

    menuItems = [elem for elem in menuItems if elem.target.endswith(".m4a")] 

    return Menu(menuItems)

def main(mainscreen):
    logger = Logger("./log.txt")

    mopidy = MopidyProxy(logger, "http://hunchcorn.local:6680/mopidy/rpc")

    screen = Screen(21, 4)

    menu = arrange_menus(mopidy)
    wire_up_menus(menu, screen)

    key = ''
    while True:
        if key == ord('q'):
            break
        elif key == ord('j'):
            menu.active_index += 1
        elif key == ord('k'):
            menu.active_index -= 1
        elif key == 10:
            activeItem = menu.items[menu.active_index]
            if not activeItem.child_menu is None:
                menu = activeItem.child_menu
                screen.clear()
            elif activeItem.method == "custom.togglepause":
                mopidy.toggle_pause()
            elif activeItem.method == "core.tracklist.add":
                mopidy.post("core.tracklist.clear")
                mopidy.post(activeItem.method, activeItem.target)
                mopidy.play()
            else:
                mopidy.post(activeItem.method)
        elif key == ord('u'):
            if not menu.parent_menu is None:
                menu = menu.parent_menu
                screen.clear()

        # menu bounds check and scrolling
        if menu.active_index >= len(menu.items):
            menu.active_index = len(menu.items) - 1
        elif menu.active_index >= menu.viewtop_index + screen.height:
            menu.viewtop_index = 1 + menu.active_index - screen.height
        elif menu.active_index < 0:
            menu.active_index = 0
        elif menu.active_index < menu.viewtop_index:
            menu.viewtop_index = menu.active_index

        draw_menu_to_screen(screen, menu)
        key = screen.get_char()

if __name__ == "__main__":
    wrapper(main)