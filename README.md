# CLITube

[![travis](https://travis-ci.org/NiZiL/clitube.svg)](https://travis-ci.org/NiZiL/cliitube)


A curses-based interface to browse YouTube, with vi-like keybindings.  
Powered by [mplayer](http://www.mplayerhq.hu/) and [youtube-dl](https://rg3.github.io/youtube-dl/).

![screenshoot](https://raw.githubusercontent.com/NiZiL/clitube/master/clitube.gif)


### Installation

WARNING: CLITube have been only tested with python3 ! There is no python2-compability guaranteed !

##### Using pip

```bash
pip install clitube
```

##### Manual

```bash
git clone https://github.com/NiZiL/clitube.git
cd clitube
[sudo] make install
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
| search  | search on Youtube |
| quit (q)| quit |
| next (n)| next soundtrack on the playlist |
| previous (p) | previous soundtrack on the playlist |
| clear (clr) | clear the playlist |


### Roadmap

- Playlist manipulation
- Search results filtering
- Real vi-like keybinding (e.g. :2n)
- Download