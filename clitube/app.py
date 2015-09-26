# -*- coding: utf-8 -*-

import requests
import re
import youtube_dl
import os
import subprocess
import curses

FNULL = open(os.devnull, 'wb')
pattern_id = re.compile("(?<=data-context-item-id=\")[\w-]{11}(?=\")")
pattern_name = re.compile("(?<=dir=\"ltr\">).*(?=</a><span)")
search_url = "https://www.youtube.com/results?filters=video&search_query={}"
video_url = "https://www.youtube.com/watch?v={}"


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


def unquote(s):
    return s.replace('&amp;', '&')


def youtube_search(search):
    r = requests.get(search_url.format(search))
    if r.status_code == 200:
        return zip(re.findall(pattern_id, r.text),
                   map(unquote, re.findall(pattern_name, r.text)))
    else:
        raise Exception("YouTube is broken :(")


def init():
    subprocess.call(['mkdir', '/tmp/clitube'],
                    stdout=FNULL,
                    stderr=FNULL)


def init_ydl():
    options = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'outtmpl': '/tmp/clitube/%(id)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True
    }
    return youtube_dl.YoutubeDL(options)


def main(stdscr):
    ydl = init_ydl()
    player = None

    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.curs_set(False)

    height, width = stdscr.getmaxyx()

    stdscr.clear()
    stdscr.addstr(0, int(width/2)-4, u"CLItube", curses.color_pair(1))
    stdscr.refresh()

    items = []
    position = 0
    selected = []

    while True:
        # render
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
            uid = items[position].uid
            name = '/tmp/clitube/%s' % uid
            url = video_url.format(uid)
            subprocess.Popen(['youtube-dl',
                              url
                              '-f', 'bestaudio',
                              '-x',
                              '-o', name],
                             stdout=FNULL, stderr=FNULL)
            if player is not None:
                player.kill()
            player = subprocess.Popen(['mplayer', name],
                                      stdout=FNULL, stderr=FNULL)

        elif c == ord('/'):
            stdscr.addstr(height-1, 0, u"search: ")
            search = ""

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

            if search != "":
                items = []
                for uid, name in youtube_search(search):
                    items.append(Item(uid, name))
        stdscr.refresh()

    if player is not None:
        player.kill()


def start():
    init()
    curses.wrapper(main)
