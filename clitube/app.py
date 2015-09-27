# -*- coding: utf-8 -*-

import requests
import html
import re
import youtube_dl
import os
import subprocess
import curses

FNULL = open(os.devnull, 'wb')

PATTERN_ID = re.compile("(?<=data-context-item-id=\")[\w-]{11}(?=\")")
PATTERN_NAME = re.compile("(?<=dir=\"ltr\">).*(?=</a><span)")
URL_SEARCH = "https://www.youtube.com/results?filters=video&search_query={}"
URL_VIDEO = "https://www.youtube.com/watch?v={}"

PIPE_STREAM = "/tmp/clitube-stream"


class Item(object):
    def __init__(self, uid, name):
        self._uid = uid
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def uid(self):
        return self._uid


def youtube_search(search):
    r = requests.get(URL_SEARCH.format(search))
    if r.status_code == 200:
        return zip(re.findall(PATTERN_ID, r.text),
                   map(html.unescape, re.findall(PATTERN_NAME, r.text)))
    else:
        raise Exception("YouTube is broken :(")


def init():
    try:
        os.mkfifo(PIPE_STREAM)
    except:
        pass


def play(uid):
    url = URL_VIDEO.format(uid)

    dl = subprocess.Popen(['youtube-dl', url,
                           '-o', PIPE_STREAM],
                          stdout=FNULL, stderr=FNULL)

    player = subprocess.Popen(['mplayer', '-vo', 'null', PIPE_STREAM],
                              stdout=FNULL, stderr=FNULL)

    return dl, player


def main(stdscr):
    # initialization, tmp directory, youtube-dl api
    init()
    dl = player = None

    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    curses.curs_set(False)
    stdscr.nodelay(True)

    items = []
    position = 0
    selected = []

    toplay = []

    height, width = stdscr.getmaxyx()
    redraw = True

    while True:
        # renderer
        # ugly piece of code here
        if (height, width) != stdscr.getmaxyx():
            redraw = True

        if redraw:
            height, width = stdscr.getmaxyx()

            stdscr.clear()
            stdscr.addstr(0, int(width/2)-4, u"CLItube", curses.color_pair(1))
            for i, item in enumerate(items):
                style = 0
                if i == position and i in selected:
                    style = curses.A_REVERSE | curses.color_pair(2)
                elif i == position:
                    style = curses.A_REVERSE
                elif i in selected:
                    style = curses.color_pair(2)
                stdscr.addstr(i+2, 0, item.name, style)
                stdscr.clrtoeol()
            stdscr.refresh()
            redraw = False

        # sound "engine", hum...
        if len(toplay) > 0:
            if player is None:
                dl, player = play(toplay[0].uid)
            else:
                player.poll()
                dl.poll()
                if not player.returncode is None:
                    player = None
                    toplay.pop(0)

        # controller
        c = stdscr.getch()

        if c == ord('q'):
            break

        elif c == ord('j') or c == curses.KEY_DOWN:
            if len(items) > 0:
                position += 1
                position %= len(items)

        elif c == ord('J') or c == curses.KEY_NPAGE:
            if len(items) > 0:
                position = len(items)-1

        elif c == ord('k') or c == curses.KEY_UP:
            if len(items) > 0:
                position -= 1
                position %= len(items)

        elif c == ord('K') or c == curses.KEY_PPAGE:
            position = 0

        elif c == ord(' '):
            if position in selected:
                selected.remove(position)
            else:
                selected.append(position)

        elif c == ord('l'):
            toplay.append(items[position])

        elif c == ord('/'):
            stdscr.addstr(height-1, 0, u"search: ")
            search = ""

            stdscr.nodelay(False)
            c = stdscr.getch()

            while c != ord('\n'):
                if c == curses.KEY_BACKSPACE:
                    search = search[:-1]
                else:
                    search += chr(c)
                stdscr.addstr(height-1, 8, search)
                stdscr.clrtoeol()

                c = stdscr.getch()

            stdscr.deleteln()
            stdscr.nodelay(True)

            if search != "":
                items = []
                for uid, name in youtube_search(search):
                    items.append(Item(uid, name))
                redraw = True

    if not player is None:
        player.kill()


def start():
    curses.wrapper(main)
