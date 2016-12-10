# Master Control by Henry Kroll

Master Control studio is a TV station in a box. It generates a GUI with mixer knobs and controls for gstreamer plugins playing and mixing live multimedia streams on Linux.

create, launch, test, and control running instances of (short list)

* Internet radios
* image slide shows
* DVD players
* HD webcam recorders
* timelapse video recorders
* desktop screen recorders
* spectrum analyzers, oscilliscopes
* live special effects panels

In addition, Master Control can

* edit text with it's built-in editor
* save and load multimedia pipelines
* generate mixer panels, pads, tweak
* combine various effects
    
Capabilities inherited from GStreamer, not limited to

* splitting audio from video files
* audio filters, mixers, converters
* video filters, mixers, converters
* broadcasting webm, videoconferenceing
* mixing and muxing, streaming live videos
* write files, multiple sources, sinks
* filtering, removing noise
* picture-in-picture, subtitles
* synthesizing speech (requires festival)
* voice recognition subtitles (requires pocketsphinx)
* capturing DV via firewire, transcoding.
* motion sensing
* face recognition (requires openCV)
* ... limitless other things

## Installation

Master Control is fully cross-platform, open-source, and released 
under the Gnu Public License, Version 3. The following packages, upon 
which Master Control depends, may be downloaded, or compiled for just 
about any operating system.

* [2.7](Python)(http://www.python.org/)
* [pygtk2](http://www.pygtk.org/)
* [gstreamer, including gstreamer-python](http://gstreamer.freedesktop.org/)
* [gtksourceview2](http://gtksourceview.sourceforge.net/)

On Fedora, for example, install these dependencies.

{{{
su -c 'yum -y install pygtk2 gstreamer-python gstreamer-plugins-\* gstreamer-ffmpeg pygtksourceview gtksourceview2'
}}}

Windows builds of these dependencies are available from 
[ossbuild](https://code.google.com/p/ossbuild/).

Master Control is maintained on 
[GitHub](https://github.com/themanyone/master_control/). The latest 
version may be obtained using git: `git clone 
https://github.com/themanyone/master_control`

Or download the .zip file: [Download](https://github.com/themanyone/master_control/archive/master.zip)

## Upgrade

Master Control's capabilities will continue to grow as new GStreamer 
plugins become available. We are developing our own motion tracking 
plugin, and non-linear editing may already be possible via 
[GNonLin](http://freecode.com/projects/gnonlin).

## Usage

There is no desktop icon yet. Right-click on the desktop to create one.
Launching the program may be done via the Python interpreter.

   `python master_control.py [args]`

New: A file name, or raw pipeline data, may now be supplied on the 
command line, similar to `gst-launch`. Master Control will 
automatically determine whether a valid file name, or raw pipeline 
description, has been supplied.

Choose a mode from the drop-down menu, for example, simple webcam 
viewer. The application should start displaying an image from the 
webcam. The editor's contents will change. Tabs will appear. Clicking 
on the tabs reveals panels of spin buttons and sliders to tweak and 
adjust every possible setting of the running GStreamer Pipeline.

Panels may be "popped-out" into their own window from the `View` menu.

Windows note: [ossbuild](https://code.google.com/p/ossbuild/) contains 
a build system to support GStreamer for Windows. To make the webcam 
work on Windows with ossbuild, change `v4l2src` to `ksvideosrc`.

## Known Issues

Master Control's HD webcam recorder may not work for everyone. It 
assumes the webcam can hardware-encode motion jpeg (MJPEG) video. If 
it does not work, try `video/x-raw-yuv` instead of the `image/jpeg` 
caps, and get rid of the `jpegdec` decoder. To discover the webcam's 
capabilities, use `v4l2-ctl --list-formats-ext`. In the future, we 
may use camerabin, or another such auto-detecing element.

[More info about transcoding with Gstreamer.](http://gentrans.sourceforge.net/docs/head/manual/html/howto.html)

[Gstreamer Cheat Sheet](http://wiki.oz9aec.net/index.php/Gstreamer_cheat_sheet)

## GStreamer Pipelines

According to the 
[file:///usr/share/doc/gst-entrans-1.0.2/html/howto.html 
documentation that installs with entrans], a GStreamer Pipeline is a 
directed graph of media handlers or plugins (elements). Each element 
has "pads" which are kind of like plugs and sockets that connect them 
together. An exclamation point, "!" behaves like a "pipe symbol" 
connecting the elements' "src" and "sink" pads. See the man pages for 
`gst-launch` for more information about constructing GStreamer pipelines.

## Help on Elements

Double-click on `v4l2src` to highlight it in the Master Control editor. 
Press Ctrl+I, or navigate to Help -> Inspect selected. A 
search-able window will pop up describing the `v4l2src` plugin and specifications. This is for convenience. The same information 
may be obtained by typing "gst-inspect v4l2src" in a terminal window.
   
Scroll down to where gst-inspect shows information about brightness 
and contrast. These values may be specified in the pipeline at 
startup, or adjusted in the tabs during runtime. Try it out. Change 
the first stanza in the editor to "v4l2src brightness=200".

## Transport Mechanism

Press the F5 key to stop, and re-start (refresh) the stream. This is 
the same as pressing the Stop and Play buttons. The interface needs 
some help. Right now the fast-forward, loop, and rewind buttons may be found under the `Go` menu.

## Use Tabs

Click on the v4l2src tab and adjust values of brightness, and contrast to suit.

## Error Handling

Master Control pipelines are equivalent to running entrans in raw 
mode. There is some rudimentary error handling, and auto-plugging of 
elements is accomplished by using plugins like playbin and 
autoaudiosrc. If a pipeline doesn't work, try experimenting. The 
majority of problems result from mis-matching of elements. Usually, a 
src or filter element is supplying a format that the next one in the 
chain does not understand. A good reading of the GStreamer 
documentation will help to minimize errors.

## Matching Caps

It is recommended that users inspect (Ctrl-I) the src and sink 
capabilities (caps) of the elements they wish to connect. Usually, 
elements will auto-negotiate, but sometimes it is necessary to 
specify caps, e.g. " ! video/x-raw-yuv,format=(fourcc)I420" between 
them. Make sure the upstream element in the chain is sending out a 
format that the receiving elements are compatible with. When there 
are no matching caps, then some other conversion element, such as 
"ffmpegcolorspace" may be inserted between elements to supply the 
matching caps.