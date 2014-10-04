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
    s=str(s)
    s=s.replace('"','\'')
    return s

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
def selector_widget(liststore, active=0, cols=1):
    widget=gtk.ComboBox(liststore)
    for x in range(0, cols):
        cell = gtk.CellRendererText()
        widget.pack_start(cell, True)
        widget.add_attribute(cell, 'text', x)
    if active:
        cell = gtk.CellRendererText()
    return widget
def make_model(data):
    m = gtk.ListStore(str, str)
    for pair in data:
        i = m.append()
        m.set_value(i, 0, pair[0])
        m.set_value(i, 1, pair[1])
    return m
def ypack(parent, control, label, expand=False, controlexpand=False, y=6):
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
        ypack.vbox=gtk.VBox()
        parent.pack_start(ypack.vbox, False)
        ypack.vbox.show()
    hbox=gtk.HBox()
    hbox.pack_end(control, controlexpand)
    hbox.pack_start(label, False)
    ypack.vbox.pack_start(hbox, expand)
    hbox.show_all()
    ypack.packed += 1
    if ypack.packed > y:
        del ypack.vbox
    return
def vpack(parent, control, label, expand=False, controlexpand=True):
    """ pack control in VBox with label underneath """
    box=gtk.VBox()
    box.pack_end(label, False)
    box.pack_end(control, controlexpand)
    parent.pack_start(box, expand)
    box.show_all()
    return box
def get_selected(textview):
    buf=textview.get_buffer()
    s,e=buf.get_selection_bounds()
    return buf.get_text(s,e)
def text_window(title, text, search=False, help_cb=False, width=600, height=400):
    """Display a scrollable, optionally searchable text window.
    help_cb: optional callback to do something with searched term"""
    w=gtk.Window()
    w.set_title(title)
    w.set_size_request(width,height)
    # vbox
        # hbox
            # searchbox, searchbutton
        # scroll
            # textview
    vbox=gtk.VBox()
    hbox=gtk.HBox()
    scroll=gtk.ScrolledWindow()
    textview=gtk.TextView()
    tb=textview.get_buffer()
    if search_cb:
        searchbox=gtk.Entry()
        searchbutton=gtk.Button("_Search")
        hbox.pack_start(searchbox,False)
        hbox.pack_start(searchbutton,False)
        # searchbox.connect("changed",search_cb,searchbox,textview)
        searchbutton.connect("clicked",search_cb,searchbox,textview)
    if help_cb:
        helpbutton=gtk.Button("_Inspect Selected")
        hbox.pack_start(helpbutton,False)
        helpbutton.connect("clicked",help_cb,textview)
    vbox.pack_start(hbox,False)
    vbox.pack_start(scroll,True,True)
    scroll.add(textview)
    w.add(vbox)
    tb.set_text(text)
    w.show_all()
    w.present()
    return w
def search_cb(button,searchbox,textview=None):
    txt = searchbox.get_text()
    tb=textview.get_buffer()
    try:
        s,s = tb.get_selection_bounds()
    except:
        s,e = tb.get_bounds()
    try:
        s,e = s.forward_search(txt,0)
        tb.select_range(s,e)
        textview.scroll_to_iter(e,0.3)
    except:
        pass
def build_menus(window, callback, menus):
    """Build menus from a dictionary"""
    me = gtk.MenuBar()
    for (label,icon),submenus in menus:
        menu=gtk.ImageMenuItem(label)
        me.append(menu)
        menu.set_image(gtk.image_new_from_stock(
        icon,gtk.ICON_SIZE_MENU))
        drop_menu = gtk.Menu()
        menu.set_submenu(drop_menu)
        drop_menu.show()
        a=gtk.AccelGroup()
        window.add_accel_group(a)
        for (label, ctl_key, icon) in submenus:
            acc,mods=gtk.accelerator_parse(ctl_key)
            acc_label=gtk.accelerator_get_label(acc,mods)
            submenu = gtk.ImageMenuItem(label,a)
            submenu.add_accelerator("activate",a,acc,mods,gtk.ACCEL_VISIBLE)
            drop_menu.add(submenu)
            submenu.set_image(gtk.image_new_from_stock(
            icon,gtk.ICON_SIZE_MENU))
            submenu.show()
            submenu.connect("activate",callback, acc_label)
    return me