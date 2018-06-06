#!/usr/bin/env python3

import json
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from time import sleep

from logger import Logger
from menu import Menu
from menu import MenuItem
from mopidyproxy import MopidyProxy    
from mopidypage import MopidyPage
from pagemanager import PageManager
from webserver import WebServer

mode = "screen" # "lcd"
mode = "lcd"

if mode == "lcd":
    import RPi.GPIO as GPIO
    from lcddriver import lcd
else:
    from screen import Screen
    from curses import wrapper

def arrange_menus(mopidy):
    menuitem_radmac = MenuItem("RadMac")
    menuitem_radmac.child_menu = menu_for_tracks_at_uri(mopidy, "file:///media/data/get-iplayer-downloads")

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
    menuitem_playlists.child_menu = menu_for_playlists(mopidy)

    return Menu([
                menuitem_radio,
                MenuItem("Play/Pause", "custom.togglepause"),
                menuitem_playlists,
                MenuItem("Artists")
    ])

def wire_up_menus(menu, screen_width):
    first_item = True
    for menu_item in menu.items:
        if first_item:
            menu_item.active = True
            first_item = False
        if not menu_item.child_menu is None:
            menu_item.text = menu_item.text.ljust(screen_width - 5) + ">>"
            menu_item.child_menu.parent_menu = menu
            wire_up_menus(menu_item.child_menu, screen_width)
        menu_item.text = menu_item.text.ljust(screen_width)

def menu_for_tracks_at_uri(mopidy, mopidy_folder_uri):
    response = mopidy.post("core.library.browse", mopidy_folder_uri)
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

def menu_for_playlists(mopidy):
    response = mopidy.post("core.playlists.get_playlists")
    response_json = json.loads(response)
    sorted_response_json = sorted(response_json["result"], key=lambda x: x["name"])
    menu_items = list(map(
        lambda i: MenuItem(
            i["name"],
            "custom.addplaylist",
            i["uri"]),
        sorted_response_json))

    return Menu(menu_items)

menu_cmd = 0
def up_callback(channel):
    global page_manager
    page_manager.up()

def down_callback(channel):  
    global page_manager
    page_manager.down()

def select_callback(channel):
    global page_manager
    page_manager.select()

def back_callback(channel):
    global page_manager
    page_manager.back()

def configure_gpio():
    GPIO.setmode(GPIO.BCM)  
  
    # GPIO 23 & 24 set up as inputs. One pulled up, the other down.  
    # 23 will go to GND when button pressed and 24 will go to 3V3 (3.3V)  
    # this enables us to demonstrate both rising and falling edge detection  
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.add_event_detect(27, GPIO.RISING, callback=back_callback, bouncetime=50)  
    GPIO.add_event_detect(22, GPIO.RISING, callback=select_callback, bouncetime=50)  
    GPIO.add_event_detect(23, GPIO.RISING, callback=down_callback, bouncetime=50)  
    GPIO.add_event_detect(24, GPIO.RISING, callback=up_callback, bouncetime=50)  

def main(win):
    global menu_cmd
    global page_manager
    print("start")
    logger = Logger("./log.txt")

    pool = ThreadPoolExecutor(5)
    futures = []

    if mode == "lcd":
        screen = lcd()
        configure_gpio()
    else:
        screen = Screen(20, 4)

    mopidy = MopidyProxy(logger, "http://hunchcorn.local:6680/mopidy/rpc")

    menu = arrange_menus(mopidy)
    wire_up_menus(menu, screen.width)

    webserver = WebServer(menu, mopidy)
    futures.append(pool.submit(webserver.run))

    main_page = MopidyPage(menu, mopidy)
    page_manager = PageManager(screen, main_page)
    futures.append(pool.submit(page_manager.run))

    while True:
        if mode == "lcd":
            sleep(5)
        else:
            key = screen.get_char()

            if key == ord('q'):
                webserver.stop()
                page_manager.stop()
                break
            elif key == ord('j'):
                page_manager.down()
            elif key == ord('k'):
                page_manager.up()
            elif key == 10: # enter
                page_manager.select()
            elif key == ord('u'):
                page_manager.back()

if __name__ == "__main__":
    if mode == "lcd":
        main(None)
        GPIO.cleanup()
    else:
        wrapper(main)


#try:  
#    print "Waiting for falling edge on port 23"  
#    GPIO.wait_for_edge(23, GPIO.FALLING)  
#    print "Falling edge detected. Here endeth the second lesson."  
#  
#except KeyboardInterrupt:  
#    GPIO.cleanup()       # clean up GPIO on CTRL+C exit  