#!/usr/bin/env python
# -*- coding: utf-8 -*-
# hklib
# Henry Kroll's pygtk library classes and functions
# usage: import hklib

# Copyright (c) 2013, 2014 Henry Kroll III, http://www.TheNerdShow.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import gtk

def unquote(s):
    s = str(s)
    s = s.replace('"', '\'')
    return s

class VideoWindow(gtk.Window):
    def __init__(self, parent):
        self.p = parent
        gtk.Window.__init__(self)
        self.set_default_size(320, 240)
        self.set_title("Preview")
        self.connect("delete-event", self.destroy_cb)
        self.vbox = gtk.VBox()
        self.add(self.vbox)
        self.connect("key-press-event", self.destroy_cb)
    def destroy_cb(self, a, b):
        self.p.toggle_grab()
        a.hide()
        return True

class VideoWidget(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.imagesink = None
        self.unset_flags(gtk.DOUBLE_BUFFERED)

    def do_expose_event(self, event):
        if self.imagesink:
            self.imagesink.expose()
            return False
        else:
            return True

    def set_sink(self, sink):
        try:
            assert self.window.xid
        except AttributeError:
            self.show_all()
        self.imagesink = sink
        self.imagesink.set_xwindow_id(self.window.xid)

class switch(object):
    """Implements switch statement in Python
    http://code.activestate.com/recipes/410692/"""
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration
    
    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False    
def selector_widget(liststore, cols = 1, icon = 0):
    widget = gtk.ComboBox(liststore)
    if icon == 1:
        cell = gtk.CellRendererPixbuf()
        widget.pack_start(cell, False)
        widget.add_attribute(cell, 'pixbuf', 0)
    for x in range(icon, cols):
        cell = gtk.CellRendererText()
        widget.pack_start(cell, True)
        widget.add_attribute(cell, 'text', x)
    return widget
def make_model(data, icon = 0):
    if icon == 1:
        m = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
    else:
        m = gtk.ListStore(str, str)
    for pair in data:
        i = m.append()
        m.set_value(i, icon, pair[0])
        m.set_value(i, icon+1, pair[1])
        if icon == 1:
            gw = gtk.Image()
            try:
                pair[2]
            except IndexError:
                pb = gw.render_icon(gtk.STOCK_OK, gtk.ICON_SIZE_MENU)
            else:
                pb = gw.render_icon(pair[2], gtk.ICON_SIZE_MENU)
            m.set_value(i, 0, pb)
    return m
def ypack(parent, control, label, expand = False, controlexpand = False, y = 6):
    """ pack up to y controls in VBox with label right """
    if not parent:
        try:
            del ypack.vbox
        except:
            pass
        return
    try:
        ypack.vbox
    except:
        ypack.packed = 0
        ypack.vbox = gtk.VBox()
        parent.pack_start(ypack.vbox, False)
        ypack.vbox.show()
    hbox = gtk.HBox()
    hbox.pack_end(control, controlexpand)
    hbox.pack_start(label, False)
    ypack.vbox.pack_start(hbox, expand)
    hbox.show_all()
    ypack.packed += 1
    if ypack.packed > y:
        del ypack.vbox
    return
def vpack(parent, control, label, expand = False, controlexpand = True):
    """ pack control in VBox with label underneath """
    box = gtk.VBox()
    box.pack_end(label, False)
    box.pack_end(control, controlexpand)
    parent.pack_start(box, expand)
    box.show_all()
    return box
def get_selected(textview):
    buf = textview.get_buffer()
    try:
        s, e = buf.get_selection_bounds()
    except ValueError:
        return None
    return buf.get_text(s, e)
class TextWindow(gtk.Window):
    """Display a scrollable, optionally searchable text window.
    help_cb: optional callback to do something with searched term"""
    def __init__(self, title, text, help_cb = False,
    width = 600, height = 400):
        gtk.Window.__init__(self)
        self.set_default_size(width, height)
        self.set_title(title)
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        scroll = gtk.ScrolledWindow()
        self.textview = textview = gtk.TextView()
        tb = textview.get_buffer()
        if help_cb:
            searchbox = gtk.Entry()
            accel_group = gtk.AccelGroup()
            self.add_accel_group(accel_group)
            self.add_accelerator("activate-default", accel_group, ord('F'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
            self.add_accelerator("activate-default", accel_group, ord('S'), gtk.gdk.MOD1_MASK, gtk.ACCEL_VISIBLE)
            self.add_accelerator("activate-default", accel_group, 13, 0, gtk.ACCEL_VISIBLE)
            searchdown = gtk.Button("Dow_n")
            searchdown.set_flags(gtk.CAN_DEFAULT)
            self.set_default(searchdown)
            searchup = gtk.Button("U_p")
            helpbutton = gtk.Button("_Inspect Selected")
            closebutton = gtk.Button("Close _window")
            hbox.pack_start(searchbox, False)
            hbox.pack_start(searchdown, False)
            hbox.pack_start(searchup, False)
            hbox.pack_start(helpbutton, False)
            hbox.pack_start(closebutton, False)
            # events
            helpbutton.connect("clicked", help_cb, textview)
            closebutton.connect("clicked", self.destroy_cb)
            closebutton.add_accelerator("clicked", accel_group, ord('W'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
            searchbox.connect("icon-release", self.search_cbi)
            searchbox.connect("activate", self.search_cbi, 1, None)
            searchdown.connect("clicked", self.search_cb, searchbox, True)
            searchup.connect("clicked", self.search_cb, searchbox, False)
        else:
            self.connect("key-press-event", self.key_event)
            textview.set_editable(False)
        vbox.pack_start(hbox, False)
        vbox.pack_start(scroll, True, True)
        scroll.add(textview)
        self.add(vbox)
        tb.set_text(text)
        self.show_all()
        self.present()
    def search_activate(self, entry):
        entry.grab_focus()
    def search_cbi(self, entry, icon_pos, event):
        self.search_cb(None, entry, icon_pos)
    def search_cb(self, button, searchbox, down=True):
        txt = searchbox.get_text()
        tb = self.textview.get_buffer()
        try:
            s, e = tb.get_selection_bounds()
        except ValueError:
            s, e = tb.get_bounds()
        if down:
            try:
                s, e = e.forward_search(txt, 0)
            except TypeError:
                s, e = s.forward_search(txt, 0)
        else:
            try:
                s, e = s.backward_search(txt, 0)
            except TypeError:
                s, e = e.backward_search(txt, 0)
        # hack: select whole item from space up until :
        try:
            s, s = s.backward_search(" ", 99)
            e, e = e.forward_search(":", 99)
        except TypeError:
            return
        # end hack
        e.backward_char()
        tb.select_range(s, e)
        self.textview.scroll_to_iter(e, 0.3)
        # except:
            # pass
    def destroy_cb(self, args=None, u=None):
        self.destroy()
    def key_event(self, widget, event=None):
        if event.string == '\x17': # Ctrl-W
            self.destroy()
def build_menus(window, callback, menus):
    """Build menus from a dictionary"""
    me = gtk.MenuBar()
    for (label, icon), submenus in menus:
        menu = gtk.ImageMenuItem(label)
        me.append(menu)
        menu.set_image(gtk.image_new_from_stock(
        icon, gtk.ICON_SIZE_MENU))
        drop_menu = gtk.Menu()
        menu.set_submenu(drop_menu)
        drop_menu.show()
        a = gtk.AccelGroup()
        window.add_accel_group(a)
        for (label, ctl_key, icon) in submenus:
            acc, mods = gtk.accelerator_parse(ctl_key)
            acc_label = gtk.accelerator_get_label(acc, mods)
            submenu = gtk.ImageMenuItem(label, a)
            submenu.add_accelerator("activate", a, acc, mods, gtk.ACCEL_VISIBLE)
            drop_menu.add(submenu)
            submenu.set_image(gtk.image_new_from_stock(
            icon, gtk.ICON_SIZE_MENU))
            submenu.show()
            submenu.connect("activate", callback, acc_label)
    return me