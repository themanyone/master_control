filesrc name=f
 ! queue
 ! decodebin
 ! tee name=t
t. ! queue ! audioconvert 
 ! autoaudiosink
t. ! queue leaky=1 ! audioconvert 
 ! spectrascope shader=2 shade-amount=4047179778 
 ! queue ! autovideoconvert ! autovideosink f
location=