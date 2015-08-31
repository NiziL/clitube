#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import os
import subprocess
import curses

pattern_id = re.compile("(?<=data-context-item-id=\")[\w-]{11}(?=\")")
pattern_name = re.compile("(?<=dir=\"ltr\">).*(?=</a><span)")
search_url = "https://www.youtube.com/results?filters=video&search_query={}"
video_url = "https://www.youtube.com/watch?v={}"
clitube_data_pipe = "/tmp/clitube-data-pipe"
clitube_cmd_pipe = "/tmp/clitube-cmd-pipe"

FNULL = open(os.devnull, 'wb')


def unquote(s):
    return s.replace('&#39;', '\'').replace('&amp;', '&')


def search_on_youtube(query):
    r = requests.get(search_url.format(query))
    if r.status_code == 200:
        name_matches = re.findall(pattern_name, r.text)
        id_matches = re.findall(pattern_id, r.text)
        return zip(name_matches, id_matches)
    else:
        raise Exception("YouTube is broken :(")


class Item(object):
    def __init__(self, name, uid):
        self._name = name
        self._uid = uid

    @property
    def name(self):
        return self._name

    @property
    def uid(self):
        return self._uid


class Player(object):
    def __init__(self):
        self._run = False
        # init the pipe between youtube-dl and mplayer
        subprocess.call(['mkfifo', clitube_data_pipe],
                        stdout=FNULL, stderr=subprocess.STDOUT)
        subprocess.call(['mkfifo', clitube_cmd_pipe],
                        stdout=FNULL, stderr=subprocess.STDOUT)

    @property
    def run(self):
        return self._run

    def play(self, uid):
        self._youtube_dl = subprocess.Popen(['youtube-dl',
                                             '-q', video_url.format(uid),
                                             '-o', clitube_data_pipe],
                                            stdout=FNULL,
                                            stderr=subprocess.STDOUT)
        self._mplayer = subprocess.Popen(['mplayer',
                                          '-vo', 'null',
                                          'input',
                                          'file={}'.format(clitube_cmd_pipe),
                                          clitube_data_pipe],
                                         stdout=FNULL,
                                         stderr=subprocess.STDOUT)
        self._run = True

    def terminate(self):
        self._youtube_dl.terminate()
        self._mplayer.terminate()
        self._run = False

    def kill(self):
        self._youtube_dl.kill()
        self._mplayer.kill()
        self._run = False


# might rename this shit :P
def do_stuff(stdscr):
    height, width = stdscr.getmaxyx()

    stdscr.clear()
    stdscr.box()
    stdscr.addstr(0, int(width/2)-4, u" CLITube ",
                  curses.color_pair(2) | curses.A_BOLD)
    stdscr.refresh()

    search_scr = curses.newwin(height-2, int(width/2), 1, 1)
    search_scr.clear()
    search_scr.box()
    search_scr.addstr(0, int(width/4)-4, u" Search ")
    search_scr.refresh()

    playlist_scr = curses.newwin(height-2, int(width/2)-2, 1, int(width/2)+1)
    playlist_scr.clear()
    playlist_scr.box()
    playlist_scr.addstr(0, int(width/4)-5, u" Playlist ")
    playlist_scr.refresh()

    return search_scr, playlist_scr


def main(stdscr):
    player = Player()

    items = []
    selected = []
    position = 0

    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.curs_set(False)

    height, width = stdscr.getmaxyx()
    search_scr, playlist_scr = do_stuff(stdscr)

    while True:
        if (height, width) != stdscr.getmaxyx():
            height, width = stdscr.getmaxyx()
            search_scr, playlist_scr = do_stuff(stdscr)

        c = stdscr.getch()

        if (height, width) != stdscr.getmaxyx():
            height, width = stdscr.getmaxyx()
            search_scr, playlist_scr = do_stuff(stdscr)

        if c == ord('q'):
            if player.run:
                player.terminate()
            break

        elif c == ord('/'):
            search_scr.addstr(height-4, 1, u"/")
            search = ""

            c = search_scr.getch()
            while c != ord('\n'):
                if c == 127: # curses.KEY_BACKSPACE: doesn't work on ubuntu ?
                    search = search[:-1]
                else:
                    search += chr(c)
                nb_space = int(width/2)-len(search)-5
                search_scr.addstr(height-4, 1,
                                  u"/" + search + u" "*nb_space)
                c = search_scr.getch()
            search_scr.addstr(height-4, 1, ' '*(int(width/2)-2))

            if search != "":
                results = search_on_youtube(search)
                items = []
                position = 0
                for name, uid in results:
                    items.append(Item(unquote(name), uid))

        elif c == ord('j') or c == curses.KEY_DOWN:
            if len(items) > 0:
                position += 1
                position %= len(items)

        elif c == ord('k') or c == curses.KEY_UP:
            if len(items) > 0:
                position -= 1
                position %= len(items)

        elif c == ord(' '):
            if position in selected:
                selected.remove(position)
            else:
                selected.append(position)

        elif c == ord('\n'):
            if player.run:
                player.terminate()
            player.play(items[position].uid)

        for line, item in enumerate(items):
            style = 0
            if line == position and line in selected:
                style = curses.A_REVERSE | curses.color_pair(1)
            elif line == position:
                style = curses.A_REVERSE
            elif line in selected:
                style = curses.color_pair(1)
            search_scr.addstr(line+1, 1,
                              item.name + " "*(int(width/2)-len(item.name)-2),
                              style)

        playlist_scr.refresh()
        search_scr.refresh()
        stdscr.refresh()

    if player.run:
        player.terminate()


if __name__ == '__main__':
    curses.wrapper(main)
