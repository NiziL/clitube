# CLITube

[![travis](https://img.shields.io/travis/NiZiL/clitube/master.svg?style=flat-square&label=master build)](https://travis-ci.org/NiZiL/clitube)
[![travis](https://img.shields.io/travis/NiZiL/clitube/dev.svg?style=flat-square&label=dev build)](https://travis-ci.org/NiZiL/clitube)
[![pypi](https://img.shields.io/pypi/v/clitube.svg?style=flat-square)](https://pypi.python.org/pypi/clitube)
[![pypi](https://img.shields.io/pypi/status/clitube.svg?style=flat-square)](https://pypi.python.org/pypi/clitube)
[![pypi](https://img.shields.io/pypi/format/clitube.svg?style=flat-square)](https://pypi.python.org/pypi/clitube)
[![pypi](https://img.shields.io/pypi/dm/clitube.svg?style=flat-square)](https://pypi.python.org/pypi/clitube)

A curses-based interface to browse YouTube, with vi-like keybindings.  
Powered by [mplayer](http://www.mplayerhq.hu/) and [youtube-dl](https://rg3.github.io/youtube-dl/).

![screenshoot](https://raw.githubusercontent.com/NiZiL/clitube/master/clitube.gif)

### Installation

**WARNING:** CLITube rely on `html.unescape()`, python3.4+ only!  
If your default `python` is python2, you'll get the message `[ERROR] CLITube requires python3.4 and above.`.
You should use `python3 setup.py install`, `python3 -m pip install` or `pip3 install` in this case.

##### Using pip

```bash
[sudo] pip install clitube
```

##### Manual

```bash
git clone https://github.com/NiZiL/clitube.git
cd clitube
[sudo] python setup.py install
```


### Key-bindings

| Key   | Action | 
|-------|--------|
| :     | enter a command |
| /     | shortcut for the search command |
| n     | load more result |
| j     | move down in the result list |
| k     | move up in the result list |
| G     | go at the last result |
| g     | go at the first result |
| SPACE | select/unselect result at current position |
| ENTER | add selected results into the playlist. If no results are selected, add result at current position |
| p     | pause |
| m     | mute/unmute |
| +     | increase volume |
| -     | decrease volume |


### Commands

| Command | Effect |
|---------|--------|
| search pattern  | search pattern on Youtube |
| quit (q)| quit |
| next (n)| next soundtrack on the playlist |
| previous (p) | previous soundtrack on the playlist |
| clear (clr) | clear the playlist |
| download (dl) file_path | download result at current position into file_path |


### Roadmap

- ~~Download~~
- Playlist manipulation
- Save & load playlist
- Search results filtering
- Real vi-like keybinding (e.g. :2n)
- Python2 compatibility
