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
PIPE_CMD = "/tmp/clitube-cmd"


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

    def display(self, size):
        delta = size - len(self._name)
        if delta < 0:
            return self._name[:size]
        else:
            return self._name + delta*' '


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
    except OSError:
        pass
    try:
        os.mkfifo(PIPE_CMD)
    except OSError:
        pass


def play(uid):
    url = URL_VIDEO.format(uid)

    dl = subprocess.Popen(['youtube-dl', url,
                           '-o', PIPE_STREAM],
                          stdout=FNULL, stderr=FNULL)

    player = subprocess.Popen(['mplayer',
                               '-vo', 'null', '-slave',
                               '-input', 'file=%s' % PIPE_CMD,
                               PIPE_STREAM],
                              stdout=FNULL, stderr=FNULL)

    return dl, player


def stop(dl, player):
    if not player is None:
        try:
            player.kill()
        except ProcessLookupError:
            pass
    if not dl is None:
        try:
            dl.kill()
        except ProcessLookupError:
            pass
    return None, None


def main(stdscr):
    init()

    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

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
                    redraw_playlist = True

        # renderer
        if (height, width) != stdscr.getmaxyx():
            stdscr.clear()

            height, width = stdscr.getmaxyx()
            search_height, search_width = height-1, int(0.6*width)
            playlist_height, playlist_width = height-1, int(0.4*width)

            redraw_clitube = True
            redraw_playlist = True
            redraw_cmd = True

        if redraw_clitube:
            if position < print_min:
                print_min = position
            elif position - print_min > search_height-3:
                print_min = position - search_height + 3

            search_scr = stdscr.subwin(search_height, search_width, 0, 0)
            search_scr.clear()
            search_scr.box()
            search_scr.addstr(0, int(search_width/2)-5, u" CLItube ",
                              curses.A_BOLD)
            for i, item in enumerate(items[print_min:print_min+search_height-2]):
                style = curses.color_pair(0)
                display = item.display(search_width-2)
                if i + print_min in selected:
                    style = curses.color_pair(2)
                    display = ' ' + display[:-1]
                if i + print_min == position:
                    style = style | curses.A_REVERSE
                search_scr.addstr(i+1, 1, display, style)

            redraw_clitube = False

        if redraw_playlist:

            if play_index-1 < pl_print_min:
                pl_print_min = max(0, play_index-1)
            elif play_index - pl_print_min > playlist_height-4:
                pl_print_min = min(len(playlist)-playlist_height+2, play_index - playlist_height + 4)

            playlist_scr = stdscr.subwin(playlist_height, playlist_width,
                                         0, search_width)
            playlist_scr.clear()
            playlist_scr.box()
            playlist_scr.addstr(0, int(playlist_width/2)-5, " Playlist ", curses.A_BOLD)

            for i, item in enumerate(playlist[pl_print_min:pl_print_min+height-3]):
                style = 0
                if i + pl_print_min == play_index:
                    style = curses.A_BOLD | curses.color_pair(3)

                display = item.display(playlist_width-2)
                playlist_scr.addstr(i+1, 1, display, style)


            redraw_playlist = False

        if redraw_cmd:
            stdscr.addstr(height-1, 0, cmd)
            stdscr.clrtoeol()

            redraw_cmd = False

            # using doupdate instead of refresh seems to reduce flickering
            # (doesn't work with addch)
            # but actually, clitube works without neither doupdate nor refresh
            # must investigate
            # curses.doupdate()

        # controller
        try:
            c = stdscr.get_wch()
        except:
            c = -1

        if cmdMode:
            if c == '\n':
                if cmd == ':q' or cmd == ':quit':
                    break

                elif cmd == ':n' or cmd == ':next':
                    if play_index < len(playlist)-1:
                        play_index += 1
                        dl, player = stop(dl, player)
                        redraw_playlist = True

                elif cmd == ':p' or cmd == ':previous':
                    if play_index > 0:
                        play_index -= 1
                        dl, player = stop(dl, player)
                        redraw_playlist = True

                elif cmd == ':clr' or cmd == ':clear':
                    dl, player = stop(dl, player)
                    play_index = 0
                    playlist = []
                    redraw_playlist = True

                elif cmd.startswith(':search '):
                    try:
                        pattern = cmd[cmd.index(' ')+1:]
                    except ValueError:
                        pattern = ''
                    if pattern != '':
                        items = []
                        selected = []
                        position = 0
                        search_engine = youtube_search(pattern)
                        for uid, name in next(search_engine):
                            items.append(Item(uid, name))
                        redraw_clitube = True

                cmd = ""
                cmdMode = False
                stdscr.deleteln()
            elif type(c) == str and ord(c) == 27:  # echap key
                cmd = ""
                cmdMode = False
                stdscr.deleteln()
            elif c == curses.KEY_BACKSPACE and len(cmd) > 1:
                cmd = cmd[:-1]
                redraw_cmd = True
            elif c != -1:
                try:
                    cmd += c
                    redraw_cmd = True
                except TypeError:
                    pass

        elif c in ('j', 'k', 'G', 'g') and len(items) > 0:
            if c == 'j' :
                position += 1
                position %= len(items)
            elif c == 'k':
                position -= 1
                position %= len(items)
            elif c == 'G':
                position = len(items)-1
            elif c == 'g':
                position = 0



            redraw_clitube = True

        elif c == ' ':
            if position in selected:
                selected.remove(position)
            else:
                selected.append(position)
            redraw_clitube = True

        elif c in ('p', 'm', '+', '-') and not player is None:
            cmd = ''
            if c == 'p':
                cmd = 'pause'
            elif c == 'm':
                cmd = 'mute'
            elif c == '+':
                cmd = 'volume +1'
            elif c == '-':
                cmd = 'colume -1'
            cmd = cmd + '\n'

            with open(PIPE_CMD, 'w') as control:
                control.write(cmd)

        elif c == '\n':
            if len(selected) == 0:
                playlist.append(items[position])
            else:
                for i in selected:
                    playlist.append(items[i])
                selected = []
            redraw_clitube = True
            redraw_playlist = True

        elif c == '/':
            cmd = ":search "
            cmdMode = True
            redraw_cmd = True

        elif c == ':':
            cmd = ":"
            cmdMode = True
            redraw_cmd = True

        elif c == 'n':
            if not search_engine is None:
                for uid, name in next(search_engine):
                    items.append(Item(uid, name))
                redraw_clitube = True

    stop(dl, player)


def start():
    try:
        os.environ['ESCDELAY']
    except KeyError:
        os.environ['ESCDELAY'] = '25'
    curses.wrapper(main)
