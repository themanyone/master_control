# -*- coding: utf-8 -*-
data = (('iRadio with 10-band EQ',
         'souphttpsrc location=http://streaming.radionomy.com/GuitarWarrior\n'
         ' ! decodebin ! tee name=t ! audioconvert \n'
         ' ! equalizer-10bands ! autoaudiosink t. ! queue ! audioconvert \n'
         ' ! synaescope shader=2 shade-amount=4047179778 \n'
         ' ! queue ! autovideoconvert ! autovideosink'),
        ('play DVD (Popup video first)',
         'playbin2 uri=dvd:// flags=7'),
        ('Simple webcam viewer',
         'v4l2src\n'
         ' ! autovideoconvert\n'
         ' ! autovideosink'),
        ('Webcam HD recorder 30fps',
         'matroskamux name=mux ! filesink location=/tmp/cam.mkv \n'
         'v4l2src num-buffers=300 \n'
         ' ! image/jpeg,framerate=30/1 \n'
         ' ! tee name=pq ! queue ! jpegparse ! mux.video_0 \n'
         'autoaudiosrc \n'
         ' ! audioconvert ! vorbisenc ! mux.audio_0 pq. ! queue leaky=1 \n'
         ' ! jpegdec ! autovideosink'),
        ('Grab audio from video',
         'filesrc location=/tmp/cam.mkv \n'
         ' ! matroskademux\n'
         ' ! vorbisdec\n'
         ' ! wavenc\n'
         ' ! filesink location=/tmp/cam.wav'),
        ('Webcam Timelapse 5->25fps',
         'matroskamux name=mux ! filesink \n'
         'location=/tmp/cam.mkv \n'
         'v4l2src\n'
         ' ! image/jpeg,width=640,height=480,framerate=5/1\n'
         ' ! videorate force-fps=25/1 drop-only=true\n'
         ' ! tee name=pq ! queue ! jpegparse ! mux.\n'
         ' pq. ! queue ! jpegdec ! autovideosink'),
        ('Audio recorder, noise gate',
         'autoaudiosrc ! ladspa-gate \n'
         'Threshold=-28.0 Decay=2.0 Hold=2.0 Attack=0.1 \n'
         ' ! tee name=t ! autoaudiosink t. ! lame ! filesink location=/tmp/out.mp3'),
        ('Live voice changer   \\m/',
         'autoaudiosrc \n'
         ' ! ladspa-tap-pitch name=pitch \n'
         'Wet-Level--dB-=20 Dry-Level--dB-=10 Semitone-Shift=-5 \n'
         ' ! autoaudiosink'),
        ('Voice change chorus with spectrascope',
         'autoaudiosrc \n'
         ' ! ladspa-tap-pitch name=pitch \n'
         'Wet-Level--dB-=20 Dry-Level--dB-=20 Semitone-Shift=12 \n'
         ' ! tee name=t ! level ! queue ! audioconvert \n'
         ' ! autoaudiosink name=sink  t. ! queue ! audioconvert \n'
         ' ! spectrascope shader=5 shade-amount=36709122 name=scope \n'
         ' ! queue ! autovideoconvert ! autovideosink name=vsink'),
        ('Image slideshow',
         'multifilesrc loop=true\n'
         'location=%05d.png\n'
         ' ! image/png,framerate=1/1\n'
         ' ! videorate\n'
         ' ! image/png,framerate=1/3\n'
         ' ! pngdec\n'
         ' ! ffmpegcolorspace\n'
         ' ! autovideosink'),
        ('Desktop screen recorder -> vp8 webm',
         'ximagesrc use-damage=0\n'
         ' ! video/x-raw-rgb,framerate=15/1\n'
         ' ! ffmpegcolorspace\n'
         ' ! video/x-raw-yuv,format=(fourcc)I420\n'
         ' ! tee name=t\n'
         ' ! vp8enc speed=5\n'
         ' ! webmmux name=mux\n'
         ' ! filesink location="/tmp/out.webm"\n'
         't. ! queue ! autovideosink\n'
         'autoaudiosrc ! level ! audioconvert ! vorbisenc\n'
         ' ! mux.audio_0'),
        ('Sound level meter, oscilliscope',
         'autoaudiosrc\n'
         ' ! level ! wavescope shader=0 ! autovideoconvert ! xvimagesink'),
        ('Streaming Ogg/Theora+Vorbis playback, tee to disk',
         'gnomevfssrc location=http://gstreamer.freedesktop.org/media/small/cooldance.ogg \n'
         ' ! tee name=tee \n'
         ' tee. ! oggdemux name=demux \n'
         ' demux. ! queue ! theoradec ! ffmpegcolorspace ! autovideosink \n'
         ' demux. ! queue ! vorbisdec ! audioconvert ! autoaudiosink \n'
         ' tee. ! queue ! filesink location=/tmp/cooldance.ogg'),
        ('Video test, YUV format',
         'videotestsrc \n'
         ' ! video/x-raw-yuv,format=(fourcc)I420 \n'
         ' ! ffmpegcolorspace ! autovideosink'),
        ('Video test, RGB format',
         'videotestsrc \n'
         ' ! video/x-raw-rgb,red_mask=0xff00 \n'
         ' ! ffmpegcolorspace \n'
         ' ! autovideosink'),
        ('Video overlays',
         'videotestsrc pattern="snow" \n'
         ' ! video/x-raw-yuv, framerate=10/1, width=200, \n'
         'height=150 ! videomixer name=mix \n'
         'sink_1::xpos=20 \n'
         'sink_1::ypos=20 sink_1::alpha=0.5 \n'
         'sink_1::zorder=3 sink_2::xpos=100 \n'
         'sink_2::ypos=100 sink_2::zorder=2 \n'
         ' ! ffmpegcolorspace ! xvimagesink videotestsrc pattern=13 \n'
         ' ! video/x-raw-yuv, framerate=10/1, width=200, height=150 \n'
         ' ! mix. videotestsrc \n'
         ' ! video/x-raw-yuv, framerate=10/1, width=640, \n'         'height=360 ! mix.'),
        ('Software scaling',
         'videotestsrc \n'
         ' ! video/x-raw-rgb,height=200,width=320 \n'
         ' ! videoscale method=2 \n'
         ' ! ffmpegcolorspace ! autovideosink'),
        ('Reencode Vorbis to mulaw, play',
         'filesrc location=/tmp/cooldance.ogg \n'
         ' ! oggdemux \n'
         ' ! vorbisdec ! audioconvert \n'
         ' ! mulawenc ! mulawdec ! autoaudiosink'),
        ('Capture DV via firewire, transcode into Ogg',
         'dv1394src \n'
         ' ! dvdemux name=demux \n'
         ' ! queue \n'
         ' ! video/x-dv,systemstream=(boolean)false \n'
         ' ! dvdec drop-factor=2 \n'
         ' ! videorate \n'
         ' ! videoscale \n'
         ' ! video/x-raw-yuv,width=360,height=288 \n'
         ' ! videoscale \n'
         ' ! video/x-raw-yuv,width=240,height=192,framerate=10.0,format=(fourcc)YUY2 \n'
         ' ! ffmpegcolorspace \n'
         ' ! theoraenc \n'
         ' ! oggmux name=mux \n'
         ' ! filesink location=/tmp/dv.ogg \n'
         ' \n'
         ' demux. \n'
         ' ! audio/x-raw-int \n'
         ' ! queue \n'
         ' ! audioconvert \n'
         ' ! vorbisenc \n'
         ' ! mux.'))
