#!/usr/bin/env python3

from curses import wrapper
import json
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from time import sleep

from logger import Logger
from screen import Screen
from lcddriver import lcd
from menu import Menu
from menu import MenuItem
from mopidyproxy import MopidyProxy    
from webserver import WebServer
import RPi.GPIO as GPIO

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
    global menu_cmd
    menu_cmd = ord('k')

def down_callback(channel):  
    global menu_cmd
    menu_cmd = ord('j')

def select_callback(channel):
    global menu_cmd
    menu_cmd = 10

def back_callback(channel):
    global menu_cmd
    menu_cmd = ord('u')

def configure_gpio():
    GPIO.setmode(GPIO.BCM)  
  
    # GPIO 23 & 24 set up as inputs. One pulled up, the other down.  
    # 23 will go to GND when button pressed and 24 will go to 3V3 (3.3V)  
    # this enables us to demonstrate both rising and falling edge detection  
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(27, GPIO.FALLING, callback=back_callback, bouncetime=300)  
    GPIO.add_event_detect(22, GPIO.FALLING, callback=select_callback, bouncetime=300)  
    GPIO.add_event_detect(23, GPIO.FALLING, callback=down_callback, bouncetime=300)  
    GPIO.add_event_detect(24, GPIO.FALLING, callback=up_callback, bouncetime=300)  

def main(win):
    global menu_cmd
    logger = Logger("./log.txt")

    pool = ThreadPoolExecutor(5)
    futures = []

    #screen = Screen(21, 4)
    screen = lcd()

    mopidy = MopidyProxy(logger, "http://hunchcorn.local:6680/mopidy/rpc")

    menu = arrange_menus(mopidy)
    wire_up_menus(menu, screen.width)

    webserver = WebServer(menu, mopidy)
    futures.append(pool.submit(webserver.run))

    configure_gpio()

    main_page = MopidyPage(menu, mopidy)
    page_manager = PageManager(screen, main_page)
    futures.append(pool.submit(page_manager.run))

    key = ''
    while True:
        if key == ord('q'):
            webserver.stop()
            page_manager.stop()
            GPIO.cleanup()
            break
        elif key == ord('j'):
            page_manager.down()
        elif key == ord('k'):
            page_manager.up()
        elif key == 10: # enter
            page_manager.select()
        elif key == ord('u'):
            page_manager.back()

#        key = screen.get_char()
        sleep(0.1)
        key = menu_cmd
        menu_cmd = 0

if __name__ == "__main__":
    wrapper(main)


#try:  
#    print "Waiting for falling edge on port 23"  
#    GPIO.wait_for_edge(23, GPIO.FALLING)  
#    print "Falling edge detected. Here endeth the second lesson."  
#  
#except KeyboardInterrupt:  
#    GPIO.cleanup()       # clean up GPIO on CTRL+C exit  