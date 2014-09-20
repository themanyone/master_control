import sys

import pygtk
pygtk.require('2.0')
import gobject
import pango
import gtk
from gtk import gdk

if gtk.pygtk_version < (2, 8):
    print "PyGtk 2.8 or later required for this example"
    raise SystemExit

try:
    import cairo
except ImportError:
    raise SystemExit("cairo required for this example")

BORDER_WIDTH = 1
MARGIN_WIDTH = 5

# A quite simple gtk.Widget subclass which demonstrates how to subclass
# and do realizing, sizing and drawing.

class level_bar(gtk.Widget):
    def __init__(self, min=-24.0, max=6.0):
        gtk.Widget.__init__(self)
        self._bottom_label = self.create_pango_layout(str(min))
        self._bottom_label.set_font_description(pango.FontDescription("Sans Serif 8"))
        self._top_label = self.create_pango_layout(str(max))
        self._top_label.set_font_description(pango.FontDescription("Sans Serif 8"))
        # initialize values
        self.min=float(min)
        self.max=float(max)
        self.value=min
        
    def set_value(self,val):
        if val < self.min:
            val = self.min
        self.value=float(val)
        self.queue_draw()

    # GtkWidget

    def do_realize(self):
        # The do_realize method is responsible for creating GDK (windowing system)
        # resources. In this example we will create a new gdk.Window which we
        # then draw on

        # First set an internal flag telling that we're realized
        self.set_flags(gtk.REALIZED)

        # Create a new gdk.Window which we can draw on.
        # Also say that we want to receive exposure events by setting
        # the event_mask
        self.window = gdk.Window(
            self.get_parent_window(),
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gdk.WINDOW_CHILD,
            wclass=gdk.INPUT_OUTPUT,
            event_mask=self.get_events() | gdk.EXPOSURE_MASK)

        # Associate the gdk.Window with ourselves, Gtk+ needs a reference
        # between the widget and the gdk window
        self.window.set_user_data(self)

        # Attach the style to the gdk.Window, a style contains colors and
        # GC contextes used for drawing
        self.style.attach(self.window)

        # The default color of the background should be what
        # the style (theme engine) tells us.
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)

    def do_unrealize(self):
        # The do_unrealized method is responsible for freeing the GDK resources

        # De-associate the window we created in do_realize with ourselves
        self.window.set_user_data(None)
        # Had to add this to make sure widget gets destroyed with parent
        self.window.destroy()

    def do_size_request(self, requisition):
        # The do_size_request method Gtk+ is calling on a widget to ask
        # it the widget how large it wishes to be. It's not guaranteed
        # that gtk+ will actually give this size to the widget

        # In this case, we say that we want to be as big as the
        # text is, plus a little border around it.
        width, height = self._bottom_label.get_size()
        requisition.width = width // pango.SCALE + BORDER_WIDTH*4
        requisition.height = height // pango.SCALE + BORDER_WIDTH*4

    def do_size_allocate(self, allocation):
        # The do_size_allocate is called by when the actual size is known
        # and the widget is told how much space could actually be allocated

        # Save the allocated space
        self.allocation = allocation

        # If we're realized, move and resize the window to the
        # requested coordinates/positions
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)

    def do_expose_event(self, event):
        # The do_expose_event is called when the widget is asked to draw itself
        # Remember that this will be called a lot of times, so it's usually
        # a good idea to write this code as optimized as it can be, don't
        # Create any resources in here.

        # In this example, draw a rectangle in the foreground color
        x, y, w, h = self.allocation
        cr = self.window.cairo_create()

        # draw the text in the middle of the allocated space
        fontw, fonth = self._bottom_label.get_pixel_size()
        cr.move_to((w - fontw)/2,0)
        cr.update_layout(self._top_label)
        cr.show_layout(self._top_label)
        
        cr.move_to((w - fontw)/2, (h - fonth))
        cr.update_layout(self._bottom_label)
        cr.show_layout(self._bottom_label)
        
        # draw a smaller rectangle and fill it up to min-max / value
        # cr = self.window.cairo_create()
        cr.set_line_width(0.0)
        cr.set_source_color(gtk.gdk.color_parse("#0F2"))
        pct = 1-abs((self.value-self.min) / (self.max - self.min))
        zero = 1-abs((self.min) / (self.max - self.min))
        offs= (h-fonth*2) * pct
        if pct<0:
            cr.set_source_color(gtk.gdk.color_parse("#F20"))
        cr.rectangle(MARGIN_WIDTH, fonth+offs, \
        w - 2*MARGIN_WIDTH, h-fonth*2-offs)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.fill()
        cr.stroke()
        if zero<100 and zero >= 0:
            cr.set_source_color(gtk.gdk.color_parse("#F88"))
            cr.rectangle(MARGIN_WIDTH, fonth,\
            w - 2*MARGIN_WIDTH, (h-fonth*2) * zero)
            cr.fill()
            cr.stroke()
            
        cr.set_source_color(self.style.fg[self.state])
        cr.rectangle(MARGIN_WIDTH, fonth,
                     w - 2*MARGIN_WIDTH, h - fonth*2)
        cr.set_line_width(1.0)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        
        cr.stroke()

gobject.type_register(level_bar)

def main(args):
    win = gtk.Window()
    win.set_default_size(100, 150)
    win.set_border_width(BORDER_WIDTH)
    win.set_title('Widget test')
    win.connect('delete-event', gtk.main_quit)

    frame = gtk.Frame("Mic Level Widget")
    win.add(frame)

    label=gtk.Label("mic-0")
    w = level_bar()    
    vbox=gtk.VBox()
    vbox.pack_start(w, True)
    vbox.pack_start(label, False)
    box=gtk.HBox()
    box.pack_start(vbox, False)
    
    frame.add(box)
    win.show_all()
    gtk.main()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
