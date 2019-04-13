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
#from webserver import WebServer

mode = "screen"
mode = "lcd"

if mode == "lcd":
    import RPi.GPIO as GPIO
    from gpiozero import Button
    from lcddriver import lcd
else:
    from screen import Screen
    from curses import wrapper

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

def togglepause_callback(channel):
    global page_manager
    page_manager.togglepause()

def configure_lcd(lcd):
    segs = [
        [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111],
        [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111, 0b11111],
        [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111, 0b11111, 0b11111],
        [0b00000, 0b00000, 0b00000, 0b00000, 0b11111, 0b11111, 0b11111, 0b11111],
        [0b00000, 0b00000, 0b00000, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111],
        [0b00000, 0b00000, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111],
        [0b00000, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111],
        [0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111]]

    for i in range(8): lcd.createChar(i, segs[i])

buttons = []
def configure_gpio():
    global buttons

    pinButtonLookup = {
        17:back_callback,
        26:select_callback,
        24:down_callback,
        9:up_callback,
        14:back_callback,
        20:togglepause_callback
    }
    for buttonPin in pinButtonLookup:
        button = Button(buttonPin, pull_up=False, bounce_time=0.05)
        button.when_pressed = pinButtonLookup[buttonPin]
        buttons.append(button)

def main(win):
    global page_manager
    print("start")
    logger = Logger("./log.txt")

    pool = ThreadPoolExecutor(5)
    futures = []

    if mode == "lcd":
        screen = lcd()
        configure_lcd(screen)
        configure_gpio()
    else:
        screen = Screen(20, 4)

    mopidy = MopidyProxy(logger, "http://hunchcorn:6680/mopidy/rpc")

    #webserver = WebServer(menu, mopidy)
    #futures.append(pool.submit(webserver.run))

    main_page = MopidyPage(mopidy, screen.width)
    page_manager = PageManager(screen, main_page, mopidy)
    futures.append(pool.submit(page_manager.run))

    while True:
        if mode == "lcd":
            sleep(5)
        else:
            key = screen.get_char()

            if key == ord('q'):
                #webserver.stop()
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
