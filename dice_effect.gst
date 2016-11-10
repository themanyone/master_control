v4l2src
 ! video/x-raw-yuv,width=640,height=480
 ! ffmpegcolorspace
 ! video/x-raw-rgb,depth=24,bpp=32
 ! dicetv
 ! ffmpegcolorspace
 ! autovideosink