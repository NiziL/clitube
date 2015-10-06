# -*- coding: utf-8 -*-


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


class ItemList(object):

    def __init__(self):
        self.clear()

    def clear(self):
        self._items = []
        self._offset = 0
        self._position = 0
        self._selected = []

    def add(self, item):
        self._items.append(item)

    def go_up(self):
        self._position -= 1
        self._position %= len(self._items)

    def go_down(self):
        self._position += 1
        self._position %= len(self._items)

    def go_top(self):
        self._position = 0

    def go_bottom(self):
        self._position = len(self._items)-1

    def is_movable(self):
        return len(self._items) > 0

    def _compute_offset(self, max_len):
        if self._position < self._offset:
            self._offset = self._position
        elif self._position-self._offset > max_len-1:
            self._offset = self._position-max_len+1

    def visible_items(self, max_len):
        self._compute_offset(max_len)
        return self._items[self._offset:self._offset+max_len]

    def select(self):
        if self._position in self._selected:
            self._selected.remove(self._position)
        else:
            self._selected.append(self._position)

    def unselect_all(self):
        self._selected = []

    def has_selection(self):
        return len(self._selected) > 0

    def selected_items(self):
        for i in self._selected:
            yield self._items[i]

    def position_item(self):
        return self._items[self._position]

    def is_selected(self, i, offset=True):
        if offset:
            i += self._offset
        return i in self._selected

    def is_position(self, i, offset=True):
        if offset:
            i += self._offset
        return i == self._position


class Playlist(object):

    def __init__(self, space_before=1):
        self._list = []
        self._iplay = 0
        self._offset = 0
        self._space_before = space_before

    def add(self, item):
        self._list.append(item)

    def is_over(self):
        return self._iplay >= len(self._list)

    def current_uid(self):
        return self._list[self._iplay].uid

    def next(self, step=1, secure=True):
        self._iplay += step
        if secure and self._iplay > len(self._list)-1:
            self._iplay = len(self._list)-1

    def previous(self, step=1, secure=True):
        self._iplay -= step
        if secure and self._iplay < 0:
            self._iplay = 0

    def _compute_offset(self, max_len):
        if self._iplay-self._space_before < self._offset:
            self._offset = max(0, self._iplay-self._space_before)
        elif self._iplay - self._offset > max_len-2:
            self._offset = min(len(self._list)-max_len, self._iplay-max_len+2)

    def visible_items(self, max_len):
        self._compute_offset(max_len)
        return self._list[self._offset:self._offset+max_len]

    def is_current(self, i, offset=True):
        if offset:
            i += self._offset
        return i == self._iplay
