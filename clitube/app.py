# -*- coding: utf-8 -*-

import requests
import html
import re
import os
import subprocess
import curses
import itertools

import clitube.model as model

FNULL = open(os.devnull, 'wb')

PATTERN_ID = re.compile("(?<=data-context-item-id=\")[\w-]{11}(?=\")")
PATTERN_NAME = re.compile("(?<=dir=\"ltr\">).*(?=</a><span)")
URL_SEARCH = "https://www.youtube.com/results?" \
             "filters=video&search_query={}&page={}"
URL_VIDEO = "https://www.youtube.com/watch?v={}"

PIPE_STREAM = "/tmp/clitube-stream"
PIPE_CMD = "/tmp/clitube-cmd"


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
    if player is not None:
        try:
            player.kill()
        except ProcessLookupError:
            pass
    if dl is not None:
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

    itemlist = model.ItemList()
    playlist = model.Playlist()

    search_engine = None
    dl = player = None

    cmdMode = False
    cmd = ""

    while True:
        # sound "engine", hum...
        if not playlist.is_over():
            if player is None:
                dl, player = play(playlist.current_uid())
            else:
                player.poll()
                dl.poll()
                if player.returncode is not None:
                    player = None
                    playlist.next()

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
            search_scr = stdscr.subwin(search_height, search_width, 0, 0)
            search_scr.clear()
            search_scr.box()
            search_scr.addstr(0, int(search_width/2)-5,
                              u" CLItube ", curses.A_BOLD)
            for i, item in enumerate(itemlist.visible_items(search_height-2)):
                style = curses.color_pair(0)
                display = item.display(search_width-2)
                if itemlist.is_selected(i):
                    style = curses.color_pair(2)
                    display = ' ' + display[:-1]
                if itemlist.is_position(i):
                    style = style | curses.A_REVERSE
                search_scr.addstr(i+1, 1, display, style)
            redraw_clitube = False

        if redraw_playlist:
            playlist_scr = stdscr.subwin(playlist_height, playlist_width,
                                         0, search_width)
            playlist_scr.clear()
            playlist_scr.box()
            playlist_scr.addstr(0, int(playlist_width/2)-5,
                                u" Playlist ", curses.A_BOLD)
            for i, item in enumerate(playlist.visible_items(playlist_height-2)):
                style = 0
                display = item.display(playlist_width-2)
                if playlist.is_current(i):
                    style = curses.A_BOLD | curses.color_pair(3)
                playlist_scr.addstr(i+1, 1, display, style)
            redraw_playlist = False

        if redraw_cmd:
            stdscr.addstr(height-1, 0, cmd)
            stdscr.clrtoeol()
            redraw_cmd = False

        # curses.doupdate()
        # using doupdate instead of refresh seems to reduce flickering
        # but neither doupdate nor refresh are required by clitube...
        # must investigate

        # controller
        try:
            c = stdscr.get_wch()
        except:
            c = -1

        if cmdMode:
            # COMMAND MODE
            if c == '\n':
                if cmd == ':q' or cmd == ':quit':
                    break

                elif cmd == ':n' or cmd == ':next':
                    playlist.next()
                    dl, player = stop(dl, player)
                    redraw_playlist = True

                elif cmd == ':p' or cmd == ':previous':
                    playlist.previous()
                    dl, player = stop(dl, player)
                    redraw_playlist = True

                elif cmd == ':clr' or cmd == ':clear':
                    playlist.clear()
                    dl, player = stop(dl, player)
                    redraw_playlist = True

                elif cmd.startswith(':search '):
                    try:
                        pattern = cmd[cmd.index(' ')+1:]
                    except ValueError:
                        pattern = ''

                    if pattern != '':
                        search_engine = youtube_search(pattern)
                        itemlist.clear()
                        for uid, name in next(search_engine):
                            itemlist.add(model.Item(uid, name))
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

        # KEY-BINDINGS
        elif c in ('j', 'k', 'G', 'g') and itemlist.is_movable():
            if c == 'j':
                itemlist.go_down()
            elif c == 'k':
                itemlist.go_up()
            elif c == 'G':
                itemlist.go_bottom()
            elif c == 'g':
                itemlist.go_top()
            redraw_clitube = True

        elif c == ' ':
            itemlist.select()
            redraw_clitube = True

        elif c in ('p', 'm', '+', '-') and player is not None:
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
            if itemlist.has_selection():
                for item in itemlist.selected_items():
                    playlist.add(item)
                itemlist.unselect_all()
                redraw_clitube = True
            else:
                playlist.add(itemlist.position_item())
            redraw_playlist = True

        elif c == ':':
            cmd = ":"
            cmdMode = True
            redraw_cmd = True

        elif c == '/':
            cmd = ":search "
            cmdMode = True
            redraw_cmd = True

        elif c == 'n':
            if search_engine is not None:
                for uid, name in next(search_engine):
                    itemlist.add(model.Item(uid, name))
                redraw_clitube = True

    stop(dl, player)


def start():
    try:
        os.environ['ESCDELAY']
    except KeyError:
        os.environ['ESCDELAY'] = '25'
    curses.wrapper(main)
