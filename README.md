# CLITube

A curses-based interface to browse YouTube, with vi-like keybindings.  
Powered by [mplayer](http://www.mplayerhq.hu/) and [youtube-dl](https://rg3.github.io/youtube-dl/).

WORK IN PROGRESS, USE AT YOUR OWN RISK

### Installation

```bash
git clone https://github.com/NiZiL/clitube.git
cd clitube
sudo make
```

### Key-bindings

| Key   | Action | 
|-------|--------|
| q     | exit |
| /     | search on YouTube |
| n     | load more result |
| j     | move down in the result list |
| k     | move up in the result list |
| G     | go at the last result |
| gg    | go at the first result |
| SPACE | select the current result |
| ENTER | add selected results into the playlist. If no results are selected, add result at current postion |
