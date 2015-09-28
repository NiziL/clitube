# -*- coding: utf-8 -*-

import requests
import html
import re
import os
import subprocess
import curses
import itertools
import contextlib

FNULL = open(os.devnull, 'wb')

PATTERN_ID = re.compile("(?<=data-context-item-id=\")[\w-]{11}(?=\")")
PATTERN_NAME = re.compile("(?<=dir=\"ltr\">).*(?=</a><span)")
URL_SEARCH = "https://www.youtube.com/results?" \
             "filters=video&search_query={}&page={}"
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
    for page in itertools.count(start=1, step=1): 
        r = requests.get(URL_SEARCH.format(search, page))
        if r.status_code == 200:
            yield zip(re.findall(PATTERN_ID, r.text),
                      map(html.unescape, re.findall(PATTERN_NAME, r.text)))
        else:
            raise Exception("YouTube is broken :(")


@contextlib.contextmanager
def delay_on(scr):
    scr.nodelay(False)
    yield
    scr.nodelay(True)


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
    print_min = 0

    selected = []

    toplay = []
    search_engine = None

    height, width = None, None

    while True:
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
                    redraw = True

        # renderer
        # ugly piece of code here
        if (height, width) != stdscr.getmaxyx():
            redraw = True

        if redraw:
            height, width = stdscr.getmaxyx()

            stdscr.clear()
            stdscr.addstr(0, int(width/2)-4, u"CLItube", curses.color_pair(1))

            if position < print_min:
                print_min = position
            elif position - print_min > height-2:
                print_min = abs(height - 2 - position)

            for i, item in enumerate(items[print_min:print_min+height-1]):
                style = 0
                if i + print_min == position and i + print_min in selected:
                    style = curses.A_REVERSE | curses.color_pair(2)
                elif i + print_min == position:
                    style = curses.A_REVERSE
                elif i + print_min in selected:
                    style = curses.color_pair(2)

                if len(item.name) > int(width/2):
                    display = item.name[:int(width/2)]
                else:
                    display = item.name + u' '*(int(width/2) - len(item.name))

                stdscr.addstr(i+1, 0, display, style)
                stdscr.clrtoeol()

            for i, item in enumerate(toplay[:height-1]):
                if len(item.name) > int(width/2)-2:
                    display = item.name[:int(width/2)-2]
                else:
                    display = item.name + u' '*(int(width/2)-2 - len(item.name))
                stdscr.addstr(i+1, int(width/2)+1, display)
                stdscr.clrtoeol()
                
            stdscr.refresh()
            redraw = False

        # controller
        c = stdscr.getch()

        if c == ord('q') or c == 27:
            break

        elif c == ord('j'):
            if len(items) > 0:
                position += 1
                position %= len(items)
            redraw = True

        elif c == ord('G'):
            if len(items) > 0:
                position = len(items)-1
            redraw = True

        elif c == ord('k'):
            if len(items) > 0:
                position -= 1
                position %= len(items)
            redraw = True

        elif c == ord('g'):
            with delay_on(stdscr):
                c = stdscr.getch()
                if c == ord('g'):
                    position = 0
                    redraw = True

        elif c == ord(' '):
            if position in selected:
                selected.remove(position)
            else:
                selected.append(position)
            redraw = True

        elif c == ord('l'):
            toplay.append(items[position])
            redraw = True

        elif c == ord('/'):
            stdscr.addstr(height-1, 0, u"search: ")
            pattern = ""

            with delay_on(stdscr):
                c = stdscr.getch()

                while c != ord('\n') and c != 27: # 27 => echap key
                    if c == curses.KEY_BACKSPACE:
                        pattern = pattern[:-1]
                    else:
                        pattern += chr(c)
                    stdscr.addstr(height-1, 8, pattern)
                    stdscr.clrtoeol()

                    c = stdscr.getch()

                stdscr.deleteln()

            if pattern != "" and c != 27:
                items = []
                search_engine = youtube_search(pattern)
                for uid, name in next(search_engine):
                    items.append(Item(uid, name))
                redraw = True

        elif c == ord('n'):
            if not search_engine is None:
                for uid, name in next(search_engine):
                    items.append(Item(uid, name))
                redraw = True


    if not player is None:
        player.kill()


def start():
    curses.wrapper(main)
