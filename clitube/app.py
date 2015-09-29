# -*- coding: utf-8 -*-

import requests
import html
import re
import os
import subprocess
import curses
import itertools

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
    init()

    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    curses.curs_set(False)
    stdscr.nodelay(True)

    height, width = None, None

    items = []
    position = 0
    print_min = 0

    selected = []

    playlist = []
    play_index = 0
    pl_print_min = 0

    search_engine = None
    dl = player = None

    cmdMode = False
    cmd = ""

    while True:
        # sound "engine", hum...
        if len(playlist) > play_index:
            if player is None:
                dl, player = play(playlist[play_index].uid)
            else:
                player.poll()
                dl.poll()
                if not player.returncode is None:
                    player = None
                    play_index += 1
                    redraw = True

        # renderer
        # ugly piece of code here
        if (height, width) != stdscr.getmaxyx():
            redraw = True

        if redraw:
            height, width = stdscr.getmaxyx()

            stdscr.clear()
            stdscr.addstr(0, int(width/2)-4, u"CLItube",
                          curses.color_pair(1) | curses.A_BOLD)

            if position < print_min:
                print_min = position
            elif position - print_min > height-3:
                print_min = abs(height - 3 - position)

            for i, item in enumerate(items[print_min:print_min+height-2]):
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


            playlist_scr = stdscr.subwin(height-2, int(width/2),
                                         1, int(width/2))
            if play_index-1 < pl_print_min:
                pl_print_min = max(0, play_index-1)
            elif play_index - pl_print_min > height-6:
                pl_print_min = abs(height - 5 - play_index)+1
            pl_print_max = pl_print_min+height-3

            for i, item in enumerate(playlist[pl_print_min:pl_print_max]):
                style = 0
                if i + pl_print_min == play_index:
                    style = curses.A_REVERSE

                if len(item.name) > int(width/2)-2:
                    display = item.name[:int(width/2)-2]
                else:
                    display = item.name + u' '*(int(width/2)-2 - len(item.name))
                playlist_scr.addstr(i+1, 1, display, style)
                playlist_scr.clrtoeol()
            playlist_scr.box()
            playlist_scr.addstr(0, int(width/4)-5, " Playlist ")

            if cmdMode:
                stdscr.addstr(height-1, 0, u':'+cmd)
                stdscr.clrtoeol()

            playlist_scr.refresh()    
            stdscr.refresh()
            redraw = False

        # controller
        try:
            c = stdscr.get_wch()
        except:
            c = -1

        if cmdMode:
            if c == '\n':
                if cmd == 'q' or cmd == 'quit':
                    break
                elif cmd == 'n' or cmd == 'next':
                    if play_index < len(playlist) -1:
                        play_index += 1
                        if not player is None:
                            try:
                                dl.kill()
                            except ProcessLookupError:
                                pass
                            try:
                                player.kill()
                            except ProcessLookupError:
                                pass
                            player = None
                        redraw = True
                    
                elif cmd == 'p' or cmd == 'previous':
                    if play_index > 0:
                        play_index -= 1
                        if not player is None:
                            try:
                                dl.kill()
                            except ProcessLookupError:
                                pass
                            try:
                                player.kill()
                            except ProcessLookupError:
                                pass
                            player = None
                        redraw = True

                elif cmd.startswith('search '):
                    try:
                        pattern = cmd[cmd.index(' ')+1:]
                    except:
                        pattern = ''
                    if pattern != '':
                        items = []
                        selected = []
                        search_engine = youtube_search(pattern)
                        for uid, name in next(search_engine):
                            items.append(Item(uid, name))
                        redraw = True
                cmd = ""
                cmdMode = False
                stdscr.deleteln()
            elif type(c) == str and ord(c) == 27: # echap key
                cmd = ""
                cmdMode = False
                stdscr.deleteln()
            elif c == curses.KEY_BACKSPACE:
                cmd = cmd[:-1]
                redraw = True
            elif c != -1:
                try:
                    cmd += c
                except:
                    pass
                redraw = True

        elif c == 'j':
            if len(items) > 0:
                position += 1
                position %= len(items)
            redraw = True

        elif c == 'G':
            if len(items) > 0:
                position = len(items)-1
            redraw = True

        elif c == 'k':
            if len(items) > 0:
                position -= 1
                position %= len(items)
            redraw = True

        elif c == 'g':
            position = 0
            redraw = True

        elif c == ' ':
            if position in selected:
                selected.remove(position)
            else:
                selected.append(position)
            redraw = True

        elif c == '\n':
            if len(selected) == 0:
                playlist.append(items[position])
            else:
                for i in selected:
                    playlist.append(items[i])
                selected = []
            redraw = True

        elif c == '/':
            cmd = "search "
            cmdMode = True
            stdscr.addstr(height-1, 0, u':'+cmd)

        elif c == ':':
            cmd = ""
            cmdMode = True
            stdscr.addstr(height-1, 0, u':'+cmd)

        elif c == 'n':
            if not search_engine is None:
                for uid, name in next(search_engine):
                    items.append(Item(uid, name))
                redraw = True


    if not player is None:
        player.kill()


def start():
    try:
        os.environ['ESCDELAY']
    except KeyError:
        os.environ['ESCDELAY'] = '25'
    curses.wrapper(main)
