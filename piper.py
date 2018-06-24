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

def configure_gpio():
    GPIO.setmode(GPIO.BCM)  

    back_pin = 17
    select_pin = 26
    down_pin = 24
    up_pin = 9
    sparebuttonleft_pin = 14
    sparebuttonright_pin = 20 

    GPIO.setup(back_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  
    GPIO.setup(select_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(down_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(up_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(sparebuttonright_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(sparebuttonleft_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    bouncetime = 300
    GPIO.add_event_detect(back_pin, GPIO.RISING, callback=back_callback, bouncetime=bouncetime)
    GPIO.add_event_detect(select_pin, GPIO.RISING, callback=select_callback, bouncetime=bouncetime)
    GPIO.add_event_detect(down_pin, GPIO.RISING, callback=down_callback, bouncetime=bouncetime)
    GPIO.add_event_detect(up_pin, GPIO.RISING, callback=up_callback, bouncetime=bouncetime)

def main(win):
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

    #webserver = WebServer(menu, mopidy)
    #futures.append(pool.submit(webserver.run))

    main_page = MopidyPage(mopidy, screen.width)
    page_manager = PageManager(screen, main_page)
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