#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name: Master Control
# Info: Master Control does it all for ultimate multimedia control.
# Status: Alpha

# Copyright (C) 2014 Henry Kroll III, http://www.TheNerdShow.com
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Soft5ware Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pygtk
pygtk.require('2.0')
import gtk, gtksourceview2
import pygst
pygst.require('0.10')
import gobject
gobject.threads_init()
import gst
import subprocess
import os, sys, codecs, re
from level import *
from hklib import *
from pipes import *
class exception_handler(Exception):
    """ exception class error trap """
    def __init__(self, reason):
        self.reason = reason
""" global variables """
appname = 'Master Control'
G_PARAM_WRITABLE = 2

class Master(object):
    """ Gstreamer Master Controller """
    open_filename=''
    grab_video_windows = True
    queue_newpipe = True
    imagesink = None
    bottom_video = VideoWidget()
    preview_video = VideoWidget()
    
    def __init__(self, argv):
        self.args = ""
        self.loop = False
        if len(argv) > 2:
            self.args = " ".join(argv[1:])
        elif len(argv) == 2:
            if os.path.isfile(argv[1]):
                with open(argv[1], 'r') as f:
                    self.args=f.read()
                self.open_filename = argv[1]
                
        # Change to executable's dir
        self.path = os.path.dirname(sys.argv[0])
        if self.path and not self.open_filename:
            os.chdir(self.path)

        # program init flow:
        # init_gui -> gst_notebook -> change_pipeline -> on_play
        self.init_gui()
        self.init_preview_window()
        self.init_msg_dialog()
        self.init_err_dialog()
        self.init_file_chooser()
        
    def init_preview_window(self):
        me = self.preview_window = VideoWindow(self)

    def init_msg_dialog(self):
        me = self.msg_dialog = gtk.Dialog("Gstreamer Message Bus", None,
            gtk.DIALOG_DESTROY_WITH_PARENT)
        me.set_default_size(400, 200)
        me.connect("delete_event",self.dialog_delete)
        me.textview = gtk.TextView()
        me.scrollbox = gtk.ScrolledWindow(gtk.Adjustment(0,0,400,1,10,10))
        me.scrollbox.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        me.scrollbox.add_with_viewport(me.textview)
        me.vbox.pack_start(me.scrollbox)
        me.scrollbox.show()
        me.textview.show()
        me.vbox.show()
    def init_err_dialog(self):
        me = self.err_dialog = gtk.Dialog("Error", None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        me.set_default_size(400, 200)
        me.connect("delete_event",self.dialog_delete)
        me.label = gtk.Label("Error label")
        me.vbox.pack_start(me.label)
        me.label.show()
    def init_file_chooser(self):
        me = self.file_chooser = gtk.FileChooserDialog(title="File Chooser for *.gst files",
        parent=self.window, action=gtk.FILE_CHOOSER_ACTION_OPEN,
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT), backend=None)
        filter=gtk.FileFilter()
        filter.add_pattern("*.gst")
        filter.add_pattern("*.txt")
        filter.add_pattern("*[A-Z]")
        me.set_filter(filter)
    def show_err(self, err):
        me = self.err_dialog
        me.label.set_text(str(err))
        me.run()
        me.hide()
    def show_msg(self, obj):
        msg = str(obj)+'\n'
        me = self.msg_dialog
        if me.get_visible():
            buf   = me.textview.get_buffer()
            lines = buf.get_line_count()
            begin = buf.get_iter_at_line(lines-2)
            end   = buf.get_iter_at_line(lines-1)
            txt   = buf.get_text(begin, end)
            if txt != msg:
                buf.insert_at_cursor(str(msg))
            # delete first line when buf gets too long
            if lines > 100:
                start = buf.get_start_iter()
                finish = buf.get_iter_at_line(1)
                buf.delete(start,finish)
            # move that scrollbar down
            obj = me.scrollbox
            gtk.idle_add(self.scroll_down,buf,obj)
    def scroll_down(self, buf, obj):
        bar = obj.get_vscrollbar()
        adj = bar.get_adjustment()
        bar.set_value(adj.get_upper())
        return False # no-repeat
    def dialog_delete(self,a,b):
        a.hide()
        return True
    def pack_controls(self, tweakbox, ele, prop):
        # add a slider for each property adjustment
        button = gtk.Button(prop.name)
        # button.set_sxize_request(80,-1)
        button.default = prop.default_value
        button.set_tooltip_text("reset default")
        button.connect("button-release-event",self.tweak_changed,(ele,prop.name))
        t=str(prop)
        WRITE = 2
        if 'GParamFloat' in t or 'GParamUInt' in t\
        or 'GParamInt' in t or 'GParamDouble' in t:
            if 'GParamUInt' in t or 'GParamInt' in t:
                digits = 0
                try:
                    adj = gtk.Adjustment(ele.get_property(prop.name),prop.minimum,prop.maximum,1.0,0,0)
                except TypeError: # xpad is not readable
                    adj = gtk.Adjustment(0.0,prop.minimum,prop.maximum,1.0,0,0)
            else:
                digits = 2
                adj = gtk.Adjustment(ele.get_property(prop.name),prop.minimum,prop.maximum,0.1,0,0)
            if 'color' in t and prop.maximum > 0xffff00:
                c = ele.get_property(prop.name)
                r = (c & 0xff0000) >> 8
                g = (c<<8 & 0xff0000) >> 8
                b = (c<<16 & 0xff0000) >> 8
                widget = gtk.ColorButton(gtk.gdk.Color(r,g,b))
                widget.connect("color-set", self.tweak_changed, (ele,prop.name))
            else:
                if 'GParamDouble' in t:
                    widget = self.init_slider(adj,digits)
                else:
                    widget = gtk.SpinButton(adj, prop.maximum / 10, digits)
                widget.connect("value-changed", self.tweak_changed, (ele,prop.name))
            widget.set_tooltip_text(prop.blurb)
            if 'GParamDouble' in t:
                vpack(tweakbox,widget,button, False)
                ypack(None,widget,button)
            else:
                ypack(tweakbox,widget,button, False)
        if 'gboolean'==prop.value_type.name:
            widget = gtk.CheckButton()
            widget.set_tooltip_text(prop.blurb)
            widget.connect("button-release-event", self.tweak_changed, (ele,prop.name))
            try:
                widget.set_active(ele.get_property(prop.name))
            except TypeError:
                pass
            ypack(tweakbox,widget,button,False,False)
        if 'GParamEnum' in t:
            liststore = gtk.ListStore(int, str)
            for r in range(0,999):
                try:
                    liststore.append((int(r), prop.enum_class(r).value_name))
                except:
                    break
            widget = selector_widget(liststore, 2)
            widget.set_active(ele.get_property(prop.name))
            widget.connect("changed", self.tweak_changed, (ele,prop.name))
            widget.set_tooltip_text(prop.blurb)
            ypack(tweakbox,widget,button,False,False)
        if 'GParamString' in t and prop.flags & 1:
            widget = gtk.Entry()
            widget.set_text(ele.get_property(prop.name) or "")
            widget.connect("changed", self.tweak_changed, (ele,prop.name))
            widget.set_tooltip_text(prop.blurb)
            ypack(tweakbox,widget,button,False,False)
        if not prop.flags & WRITE:
            try:
                widget.set_sensitive(False)
            except:
                pass

    def gst_notebook(self):
        """ notebook with gst tweak sliders for each element """
        try:
            # try to recycle it, remove all but page 1
            notebook = self.notebook
            # self.hbox0.remove(notebook)
            pages = notebook.get_n_pages()
            for x in range(1,pages):
                notebook.remove_page(-1)
        except:
            # create new notebook with page 1
            # hbox packs controls to left
            notebook = self.notebook = gtk.Notebook()
            hbox = gtk.HBox()
            vbox = gtk.VBox()
            text_scroller = gtk.ScrolledWindow(gtk.Adjustment(0,0,300,1,1,1))
            text_scroller.set_policy(gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC)
            sourceview = self.sourceview = gtksourceview2.View()
            sourceview.set_wrap_mode(gtk.WRAP_WORD)
            self.textbuf = gtksourceview2.Buffer()
            sourceview.set_buffer(self.textbuf)
            
            # set programming language of buffer
            lang_mgr = gtksourceview2.LanguageManager()
            lang_id = 'sparql'
            lang = lang_mgr.get_language(lang_id)
            self.textbuf.set_language(lang)
            self.textbuf.set_highlight_syntax(True)
            
            self.textbuf.connect("changed",self.buffer_changed)
            text_scroller.add(sourceview)
            vbox.pack_end(text_scroller,True)
            sourceview.connect("button-press-event",self.sourceview_pressed)
            self.controls = (
                ("record_button", gtk.ToolButton(gtk.STOCK_MEDIA_RECORD), self.on_play),
                ("play_button", gtk.ToolButton(gtk.STOCK_MEDIA_PLAY), self.on_play),
                ("pause_button",gtk.ToolButton(gtk.STOCK_MEDIA_PAUSE), self.on_pause),
                ("stop_button", gtk.ToolButton(gtk.STOCK_MEDIA_STOP), self.on_stop),
            )
            button_box = gtk.HBox()
            for name, widget, handler in self.controls[1:]:
                widget.connect("clicked", handler)
                widget.set_tooltip_text(handler.__doc__)
                button_box.pack_start(widget, False)
                setattr(self, name, widget)
            self.controls[0][1].connect("clicked",self.on_play)
            setattr(self,self.controls[0][0],self.controls[0][1])
            # put pipeline selector here
            dropdown = self.dropdown = selector_widget(make_model(data, 1), 2, 1)
            dropdown.connect("changed",self.change_pipeline)
            if self.args:
                self.textbuf.set_text(self.args)
                self.pipetext = self.args
                self.queue_newpipe = True
                self.on_play()
            else:
                dropdown.set_active(9)
            dropdown.set_size_request(245,20)
            button_box.pack_start(dropdown, False)
            vbox.pack_start(button_box,False)
            self.update_play_buttons(gst.STATE_PLAYING)
            hbox.pack_start(vbox,False)
            notebook.append_page(hbox,gtk.Label("editor"))
        try:
            pipe = list(self.pipeline.sorted())
        except:
            return False
        pipe.reverse()
        for ele in pipe:
            # for each element in the pipeline
            # put an HBox panel of controls in the notebook
            tweakbox = gtk.HBox(homogeneous = False)
            pads = list(ele.pads())
            padbox = gtk.VBox()
            # >>> ele = pipeline.get_by_name('mix')
            # >>> pads = list(ele.pads())
            # >>> pad = pads[1]
            for pad in pads:
                button = gtk.Button(pad.get_name())
                padbox.pack_start(button,False)
                button.set_tooltip_text(pad.__doc__)
                button.connect("button-release-event",self.pad_window, pad)
            tweakbox.pack_start(padbox,False)
            props = ele.props
            for prop in props:
                self.pack_controls(tweakbox,ele,prop)
            ypack(None,None,None,False,False)
            try:
                ele_factory_name = ele.get_factory().get_name()
            except AttributeError:
                pass
            # put element names on the tabs
            label = gtk.Label(ele.get_name())
            label.drag_source_set(gtk.gdk.BUTTON1_MASK, [("move",0,0),],
            gtk.gdk.ACTION_MOVE)
            label.drag_source_set_icon_stock(gtk.STOCK_COPY)
            notebook.append_page(tweakbox,label)
        notebook.show_all()
        self.notebook = notebook
        self.notebook.connect("switch-page",self.on_page_turned)
        return False
    def change_pipeline(self, combobox, txt=None):
        if combobox:
            title = combobox.get_model()[combobox.get_active()][1]
            self.window.set_title(title)
            txt = combobox.get_model()[combobox.get_active()][-1]
            buf = self.textbuf
            buf.set_text(txt)
        self.on_stop()
        # play button parent
        rec = self.controls[0][1]
        play = self.controls[1][1]
        recording = rec.parent
        if "filesink" not in txt:
            if recording:
                hbox = rec.parent
                hbox.remove(rec)
                hbox.pack_start(play,False)
                hbox.reorder_child(play,0)
                play.show()
            if "playbin" in txt:
                return False
            self.on_play()
        else:
            if not recording:
                hbox = play.parent
                hbox.remove(play)
                hbox.pack_start(rec,False)
                hbox.reorder_child(rec,0)
                rec.show()
        return False
    def init_slider(self, adj, digits=0):
        """Apply defaults to gtk.VScale slider widgets"""
        vscale = gtk.VScale(adj)
        vscale.set_digits(digits)
        vscale.set_update_policy(gtk.UPDATE_CONTINUOUS)
        vscale.set_value_pos(gtk.POS_TOP)
        vscale.set_draw_value(True)
        vscale.set_inverted(True)
        return vscale
    def request_video_preview(self, imagesink):
        """Capture all video sinks; add to preview panel"""
        if imagesink:
            self.imagesink = imagesink            
        if self.grab_video_windows:
            if self.bottom_video.parent != self.bottom_area:
                self.bottom_area.pack_start(self.bottom_video,True)
            if self.imagesink:
                # self.imagesink.set_xwindow_id(self.bottom_video.window.xid)
                self.bottom_video.set_sink(self.imagesink)
                self.preview_window.hide()
        else:
            self.preview_video.show()
            if self.preview_video.parent != self.preview_window.vbox:
                self.preview_window.vbox.pack_start(self.preview_video,True)
                self.preview_window.show_all()
            if self.imagesink:
                self.preview_video.set_sink(self.imagesink)
            gtk.timeout_add(150,self.window.present)
    def request_level_control(self):
        """Preview panel widgets for "level" elements in pipe"""
        try:
            self.level0
        except:
            self.level0 = level_bar(-42,6)
            box = vpack(self.bottom_area, self.level0,
            gtk.Label("level"), False)
            self.bottom_area.reorder_child(box,0)
    def file_open(self):
        """Open a file dialog"""
        response = self.file_chooser.run()
        self.file_chooser.hide()
        if response==gtk.RESPONSE_ACCEPT:
            self.open_filename = self.file_chooser.get_filename()
            with codecs.open(self.open_filename,
            encoding = 'utf-8', mode = 'r') as f:
                txt = f.read()
                self.textbuf.set_text(txt)
                self.window.set_title(appname 
                + " | " + os.path.basename(self.open_filename))
            self.queue_newpipe = True
            self.change_pipeline(False, txt)
    def file_save(self):
        """Save text buffer to disk"""
        if not self.open_filename:
            response = self.file_chooser.run()
            self.file_chooser.hide()
            if response==gtk.RESPONSE_ACCEPT:
                self.open_filename = self.file_chooser.get_filename()
            else:
                return False
        begin,end = self.textbuf.get_bounds()
        with codecs.open(self.open_filename,
        encoding = 'utf-8', mode = 'w') as f:
            f.write(self.textbuf.get_text(
            begin, end))
        self.window.set_title(appname 
        + " | " + os.path.basename(self.open_filename))
        return True # command completed successfully!
    def file_save_as(self):
        """ save under a different name """
        self.open_filename = ''
        return self.file_save()
    def on_menu_activate(self, menuitem, key):
        try:
            cmd = menuitem.get_label()
        except:
            cmd = key
        clipboard = gtk.Clipboard(
        display = gtk.gdk.display_get_default(), selection = "CLIPBOARD")
        buf = self.textbuf
        e = self.sourceview.get_editable()
        begin, end = buf.get_bounds()
        txt = buf.get_text(begin, end)
        # get tab label
        pg = self.notebook.get_current_page()
        pgw = self.notebook.get_nth_page(pg)
        name = self.notebook.get_tab_label_text(pgw)
        ele = self.pipeline.get_by_name(name)
        for case in switch(cmd):
            if case("_Open", "Ctrl+O"):
                self.textbuf.begin_not_undoable_action()
                self.file_open()
                self.textbuf.end_not_undoable_action
            elif case("_Save", "Ctrl+S"):
                self.file_save()
            elif case("Save _As", "Shift+Ctrl+S"):
                self.file_save_as()
            elif case("_Close", "Ctrl+W"):
                self.open_filename = ''
                self.window.set_title(appname)
                buf.set_text("")
            elif case("_Exit", "Ctrl+Q"):
                gtk.main_quit()
            elif case("_Undo", "Ctrl+Z"):
                if self.textbuf.can_undo():
                    self.textbuf.undo()
            elif case("_Redo", "Ctrl+Y"):
                if self.textbuf.can_redo():
                    self.textbuf.redo()
            elif case("Cu_t","Ctrl+X"):
                buf.cut_clipboard(clipboard,e)
            elif case("_Copy", "Ctrl+C"):
                buf.copy_clipboard(clipboard)
            elif case("_Paste", "Ctrl+P"):
                buf.paste_clipboard(clipboard,None,e)
            elif case("Select _All", "Ctrl+A"):
                buf.select_range(begin, end)
                self.sourceview.activate()
            elif case("_Messages", "Ctrl+M"):
                self.msg_dialog.present()
            elif case("_Popup Video","Shift+Ctrl+V"):
                self.toggle_grab()
            elif case("Popup _Tab","Shift+Ctrl+T"):
                try:
                    ele.props
                except:
                    pass
                else:
                    self.pad_window(None,None,ele)
            elif case("P_ause","Ctrl+space"):
                self.on_pause()
            elif case("_Stop","Escape"):
                self.on_stop(menuitem)
            elif case("_Loop","<Ctrl>L"):
                self.loop = not self.loop
            elif case("_Play/Rec","Ctrl+Return"):
                self.on_play()
            elif case("_Rewind","Ctrl+Left"):
                tf = gst.Format(gst.FORMAT_TIME)
                try:
                    d = self.pipeline.query_position(tf, None)[0]
                except gst.QueryError:
                    d = 0
                    nt = 0
                else:
                    nt = d - 10 * 1000000000
                if nt < 1:
                    nt = 1
                self.pipeline.seek_simple(gst.FORMAT_TIME,
                gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, nt)
            elif case("Re_start","Ctrl+R"):
                self.pipeline.seek_simple(gst.FORMAT_TIME,
                gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, 1)
            elif case("_Fast Forward","Ctrl+Right"):
                tf = gst.Format(gst.FORMAT_TIME)
                try:
                    d = self.pipeline.query_position(tf, None)[0]
                except gst.QueryError:
                    d = 0
                    nt = 0
                else:
                    nt = d + 10 * 1000000000
                self.pipeline.seek_simple(gst.FORMAT_TIME,
                gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, nt)
            elif case("R_efresh","F5"):
                self.queue_newpipe = True
                self.on_play()
            elif case("_Usage Help","Ctrl+H"):
                self.on_help("README")
            elif case("_Inspect Selected","Alt+I"):
                cmds = ["gst-inspect"]
                # txt is selection
                try:
                    bounds = self.textbuf.get_selection_bounds()
                    sel = buf.get_text(bounds[0],bounds[1])
                    cmds.append(sel)
                except:
                    try:
                        sel = ele.get_factory().get_name()
                        cmds.append(sel)
                    except:
                        pass
                try:
                    txt = subprocess.check_output(cmds)
                except CalledProcessError, NameError:
                    txt = ''
                if len(cmds) < 2:
                    tw=text_window('gst-inspect', txt, True, self.search_inspect)
                else:
                    tw=text_window(sel, txt)                   
            elif case("_Plugins","Shift+Ctrl+P"):
                txt = subprocess.check_output(["gst-inspect"])
                tw=text_window('gst-inspect', txt, True, self.search_inspect)
            elif case("_About","Shift+Ctrl+A"):
                self.on_help("ABOUT")
    def toggle_grab(self):
        self.grab_video_windows = not self.grab_video_windows
        if self.grab_video_windows:
            self.bottom_area.hide()
            self.request_video_preview(False)
            self.vertlayout.set_position(260)
            gtk.timeout_add(99,self.bottom_area.show_all)
        else:
            self.request_video_preview(False)
            self.vertlayout.set_position(900)
            gtk.timeout_add(99,self.preview_window.show_all)
    def search_inspect(self, button, textview=None):
        cmds = ["gst-inspect"]
        sel=get_selected(textview)
        cmds.append(sel)
        try:
            txt = subprocess.check_output(cmds)
            tw=text_window(sel, txt)
        except:
            pass
    def on_key(self, accelgroup, acceleratable, accel_key, accel_mods, user_param1 = None):
        cmd = gtk.accelerator_get_label(accel_key, accel_mods)
        self.on_menu_activate(cmd)
        
    def init_gui(self):
        """ Initialize the GUI components """
        self.window = gtk.Window()
        self.window.set_default_size(200, 500)
        self.window.set_title(appname + ' | ' + self.open_filename)
        self.icon = gtk.gdk.pixbuf_new_from_file(os.path.join(self.path, appname+".png"))
        self.window.set_icon(self.icon)
        self.window.connect("delete-event", self.main_quit)
        self.top_area = gtk.ScrolledWindow(gtk.Adjustment(0,0,400,1,1,1))
        self.top_area.set_placement(gtk.CORNER_BOTTOM_LEFT)
        self.window.connect("size-allocate",self.on_resize)
        self.top_area.set_policy(gtk.POLICY_ALWAYS,gtk.POLICY_NEVER)
        self.gst_notebook()
        self.top_area.add_with_viewport(self.notebook)
        self.vertlayout = gtk.VPaned()
        self.menu_bar = build_menus(self.window,self.on_menu_activate,(
            (("_File",gtk.STOCK_DIRECTORY),(
                ("_Open","<Ctrl>O",gtk.STOCK_OPEN),
                ("_Save","<Ctrl>S",gtk.STOCK_SAVE),
                ("Save _As","<Shift><Ctrl>S",gtk.STOCK_SAVE_AS),
                ("_Close","<Ctrl>W",gtk.STOCK_CLOSE),
                ("_Exit","<Ctrl>Q",gtk.STOCK_QUIT),
                )),
            (("_Edit",gtk.STOCK_EDIT),(
                ("_Undo","<Ctrl>Z",gtk.STOCK_UNDO),
                ("_Redo","<Ctrl>Y",gtk.STOCK_REDO),
                ("Select _All","<Ctrl>A",gtk.STOCK_APPLY),
                ("Cu_t","<Ctrl>X",gtk.STOCK_CUT),
                ("_Copy","<Ctrl>C",gtk.STOCK_COPY),
                ("_Paste","<Ctrl>V",gtk.STOCK_PASTE),
                )),
            (("_Go",gtk.STOCK_EXECUTE),(
                ("_Play/Rec","<Ctrl>Return",gtk.STOCK_MEDIA_PLAY),
                ("P_ause","<Ctrl>space",gtk.STOCK_MEDIA_PAUSE),
                ("_Stop","Escape",gtk.STOCK_MEDIA_STOP),
                ("Re_start","<Ctrl>R",gtk.STOCK_MEDIA_PREVIOUS),
                ("_Rewind","<Ctrl>Left",gtk.STOCK_MEDIA_REWIND),
                ("_Fast Forward","<Ctrl>Right",gtk.STOCK_MEDIA_FORWARD),
                ("_Loop","<Ctrl>L",gtk.STOCK_REDO),
                ("R_efresh","F5",gtk.STOCK_REFRESH),
                )),
            (("_View",gtk.STOCK_ZOOM_100),(
                ("_Messages","<Ctrl>M",gtk.STOCK_PROPERTIES),
                ("_Popup Video","<Ctrl><Shift>V",gtk.STOCK_DND_MULTIPLE),
                ("Popup _Tab","<Ctrl><Shift>T",gtk.STOCK_DND_MULTIPLE),
                )),
            (("_Help",gtk.STOCK_HELP),(
                ("_Usage Help","<Ctrl>H",gtk.STOCK_HELP),
                ("_Plugins","<Shift><Ctrl>P",gtk.STOCK_HELP),
                ("_Inspect Selected","<Alt>I",gtk.STOCK_HELP),
                ("_About","<Shift><Ctrl>A",gtk.STOCK_ABOUT),
                )),
            ))
        self.bottom_area = gtk.HBox()
        self.request_video_preview(False) # False = init
        tophalf = gtk.VBox()
        tophalf.pack_start(self.menu_bar, False)
        tophalf.pack_start(self.top_area, True)
        self.vertlayout.add1(tophalf)
        self.vertlayout.add2(self.bottom_area)
        self.vertlayout.show_all()
        # vertical layout refinement test
        # self.vertlayout.connect("move-handle", self.handle_moved)
        self.vertlayout.set_position(260)
        self.bottom_area.show()
        self.window.add(self.vertlayout)
        self.window.show_all()
    def on_resize(self, window, alloc):
        window = self.window.get_window()
        if not window: return
        parent = self.sourceview.get_parent()
        vscrollbar = parent.get_vscrollbar()
        hscrollbar = self.top_area.get_hscrollbar()
        dropdown_alloc = self.dropdown.get_allocation()
        vsize = (alloc[3] - 100) / 2
        if vsize < 200:
            vsize = 200
        border = 3
        hadj = alloc[2]-border
        if vscrollbar.get_property("visible"):
            hadj -= 20
        self.sourceview.set_size_request(hadj,vsize)
        self.notebook.set_size_request(-1,vsize)
        dropdown_x = alloc[2]-dropdown_alloc[0]-border
        if alloc[2]<600:
            self.dropdown.set_size_request(dropdown_x,20)
    # def handle_moved(self, paned, scrolltype):
        # pos = self.vertlayout.get_position()
        # print(pos)
    def sourceview_pressed(self, widget=None, event=None, user_param1=None):
        """Scroll Textbox Into View"""
        hscrollbar = self.top_area.get_hscrollbar()
        hscrollbar.set_value(0)
    def on_page_turned(self, page, page_num, user_param1=None):
        if page_num:
            self.vertlayout.set_position(260)
    def buffer_changed(self, buffer=None):
        self.queue_newpipe = True
    def teardown(self,obj):
        try:
            for x in obj.get_children():
                self.teardown(x)
            x.destroy()
        except:
            pass
    def notebook_teardown(self):
        notebook = self.notebook
        pages   =notebook.get_n_pages()
        for x in range(1,pages):
            w = notebook.get_nth_page(x)
            self.teardown(w)                
    def on_play(self, button=None):
        """Start"""
        if self.queue_newpipe:
            self.queue_newpipe = False
            self.pipetext = self.textbuf.get_property("text")
            try:
                self.pipeline
            except AttributeError:
                pass
            else:
                # todo: dispose any other references
                gst.message_new_eos(self.pipeline)
                self.notebook_teardown()
                bus = self.pipeline.get_bus()
                bus.remove_signal_watch()
                for x in self.watch:
                    bus.disconnect(x)
                del self.watch
                del bus
                self.pipeline.set_state(gst.STATE_NULL)
                elements = list(self.pipeline.sorted())
                for x in elements:
                    x.set_state(gst.STATE_NULL)
                    self.pipeline.unlink(x)
                del self.pipeline
                # clear bottom area
                # self.bottom_area.forall(lambda x:x.destroy())
                for x in self.bottom_area:
                    if x != self.bottom_video:
                        x.destroy()
            # wait for GUI, so we can put video on it
            gtk.idle_add(self.new_pipe)
            # put controls into notebook
            gtk.idle_add(self.gst_notebook)
        try:
            self.pipeline.set_state(gst.STATE_PLAYING)
        except AttributeError:
            pass
        return False # Return False or this will repeat
    def new_pipe(self):
        # process proprietary prop=[element, msg] specifications
        self.props=[]
        stmt = re.compile("[^ ]+=\[[^\]]+\]")
        valr = re.compile("[^ ]+")
        p = self.pipetext
        statements = stmt.findall(p)
        try:
            for x in statements:
                namepos = p.rindex('name=',0,p.index(x)) + 5
                name = valr.match(p, namepos).group(0)
                prop, vars = x.split('=')
                pad = ''
                if '::' in prop:
                    pad, prop = prop.split("::")
                msgname, test, val, var, math = vars[1:-1].split(",")
                self.props.append([name, prop, pad, msgname, test, val, var, math])
        except ValueError:
            print("name= clause not found, required for [element,msg] assignment.")
        for x in statements:
            self.pipetext = self.pipetext.replace(x,'')
        try:
            self.pipeline = gst.parse_launch(self.pipetext)
        # creative error message on fail
        except (Exception, RuntimeError) as err:
            try:
                self.pipeline = gst.parse_launch('\n\nvideotestsrc pattern=18 ! textoverlay valignment=center auto-resize=false text="There was an error.\n\n'+unquote(err)+'" ! autovideoconvert ! autovideosink')
            except:
                self.err(err)
        # watch bus messages
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        self.watch = [
        bus.connect(x,self.cb_message) for x in [
            "message::element",
            "message::eos",
            "message::state-changed",
            "sync-message::element",
        ]]
        bus.enable_sync_message_emission()
        self.pipeline.set_state(gst.STATE_PLAYING)
        gtk.timeout_add(50,self.window.present)
        return False # Return False or this will repeat
    def on_pause(self, button=None):
        """Pause"""
        self.pipeline.set_state(gst.STATE_PAUSED)
    def on_stop(self, button=None):
        """Stop"""
        recording = self.controls[0][1].parent
        try:
            if recording:
                self.pipeline.set_state(gst.STATE_READY)
                self.queue_newpipe = True
            else:
                self.pipeline.set_state(gst.STATE_PAUSED)
                self.pipeline.seek_simple(gst.FORMAT_TIME,
                gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, 1)
                if self.loop and not button:
                    self.on_play()
        except AttributeError:
            pass
    def on_help(self, file):
        """Show Help Dialog"""
        ts = gtk.gdk.CURRENT_TIME
        path = os.path.abspath(os.path.join(self.path,file))
        gtk.show_uri(None,"file://"+path,ts)
    def update_play_buttons(self, state):
        if state == gst.STATE_NULL:
            self.play_button.set_sensitive(True)
            self.record_button.set_sensitive(True)
            self.pause_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
        elif state == gst.STATE_READY:
            self.play_button.set_sensitive(True)
            self.record_button.set_sensitive(True)
            self.pause_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
        elif state == gst.STATE_PAUSED:
            self.play_button.set_sensitive(True)
            self.record_button.set_sensitive(True)
            self.pause_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
        elif state == gst.STATE_PLAYING:
            self.play_button.set_sensitive(False)
            self.record_button.set_sensitive(False)
            self.pause_button.set_sensitive(True)
            self.stop_button.set_sensitive(True)
    def cb_message(self, bus, msg):
        """Receive element messages from the bus."""
        if msg.structure is None:
            if msg.type == gst.MESSAGE_EOS:
                self.on_stop()
            return
        msgname = msg.structure.get_name()
        if msg.type == gst.MESSAGE_ELEMENT:
            if msgname == "prepare-xwindow-id":
                # Assign the viewport
                # Sync with the X server before giving the X-id to the sink
                gtk.gdk.threads_enter()
                gtk.gdk.display_get_default().sync()
                imagesink = msg.src
                imagesink.set_property("force-aspect-ratio", True)
                gtk.gdk.threads_leave()
                self.request_video_preview(imagesink)
            elif msgname[:5]=="level":
                try:
                    lvl = msg.structure['peak'][0]
                    self.level0.set_value(lvl)
                except AttributeError:
                    self.request_level_control()
            gtk.idle_add(self.show_msg,msg)
        # self.props [name, prop, pad, =msgname, obj,num, var, math]
            for x in self.props:
                obj,num,var,math = x[4:]
                if msgname==x[3] and str(msg.structure[obj])==num:
                    val = msg.structure[var]
                    val = eval("val"+math)
                    ele = self.pipeline.get_by_name(x[0])
                    name, prop, pad = x[:3]
                    if pad:
                        pads = list(ele.pads())
                        for p in pads:
                            if p.get_name() == pad:
                                p.set_property(prop, val)
                    else:
                        ele.set_property(prop, val)
        elif msg.type == gst.MESSAGE_STATE_CHANGED:
            old, new, pending = msg.parse_state_changed()
            self.update_play_buttons(new)
            self.show_msg(new)
        return gst.BUS_PASS
    def pad_window(self, widget, event, pad=None):
        """Populate Pad Window with controls"""
        dlg = gtk.Dialog(pad.get_name(), None,
            gtk.DIALOG_DESTROY_WITH_PARENT)
        dlg.set_size_request(-1,190)
        hbox = gtk.HBox()
        # >>> prop = list(pad.props)[-1]
        # >>> prop.minimum = slider_value
        for prop in list(pad.props):
            self.pack_controls(hbox,pad,prop)
        ypack(None,None,None,False,False)
        dlg.vbox.pack_start(hbox,True)
        dlg.show_all()
    def tweak_changed(self, e=None, evt=None, p=None):
        try:
            ele,prop = p
        except:
            ele,prop = evt
        if 'gtk.ColorButton' in str(type(e)):
            c = e.get_color()
            value = (c.red & 0xff00)<<8\
            | (c.green & 0xff00)\
            | (c.blue & 0xff00)>>8
        elif 'gtk.Button' in str(type(e)):
            # button pressed: set default value
            widget = e.parent.get_children()[0]
            if widget == e:
                widget = e.parent.get_children()[1]
            value = e.default
            if hasattr(widget, 'set_value'):
                widget.set_value(value)
            if hasattr(widget, 'set_active'):
                widget.set_active(value)
        elif 'gtk.ComboBox' in str(type(e)):
            value = e.get_active()
        elif 'gtk.Entry' in str(type(e)):
            value = e.get_text()
        else:
            if hasattr(e,'get_value'):
                value = e.get_value()
            else:
                value = not e.get_active()
        try:
            ele.set_property(prop,value)
        except:
            if value:
                ele.set_property(prop,int(value))
    def main_quit(self,a=None,b=None,c=None):
        try:
            self.pipeline.set_state(gst.STATE_NULL)
        except:
            pass
        gtk.main_quit()
if __name__ == "__main__":
    app = Master(sys.argv)
    gtk.main()
