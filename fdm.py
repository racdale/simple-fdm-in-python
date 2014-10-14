
import numpy as np, re, sys, os, png, itertools
import wave, scipy, scipy.io.wavfile, scipy.signal
import subprocess as sp

subj = 'sampleVid.small.mov'
workfolder = 'temp/' # to avoid syncing in dropbox
ds = 6 # downsample
cuttoff_freq = 0.75 # for butterworth filtering

## first we save the audio and split the video into frames usin ffmpeg in the shell
sp.Popen("ffmpeg -i "+subj+" -ac 1 "+workfolder+"temp.wav",shell=True)
## can take a while, so let's run a subprocess and not move on till it's done
vids = sp.Popen("ffmpeg -i "+subj+" -an -r "+str(ds)+" "+workfolder+"out%d.png",shell=True)
vids.wait()

## now loop through images and do differencing, filter, then save
body_chg = np.array([])
fls = os.listdir(workfolder+'.')
for i in range(1,len(fls)):
	print ('Processing image '+str(i))
	if 'out'+str(i)+'.png' in fls:
		im2 = png.Reader(workfolder+'out'+str(i)+'.png') # get frame
		row_count, column_count, pngdata, meta = im2.asDirect()
		im2 = np.vstack(itertools.imap(np.int16, pngdata)) # need int16 type to subtract
		if i>1:
			# may be a better way to fiddle with numpy arrays; this works
			body_chg = np.append(body_chg,np.mean(np.mean(np.abs(im2-im1),axis=1),axis=0))	
			w = png.Writer(640,360,greyscale=False)	
			# have to switch back to unsigned integer for png writer; store differenced img2-1
			w.write(file('temp/diff'+str(i-1)+'.png','wb'),itertools.imap(np.uint16,np.abs(im2-im1)))
		im1=im2 # for next frame differencing, t is now t-1
	else:
		break

## source http://azitech.wordpress.com/2011/03/15/designing-a-butterworth-low-pass-filter-with-scipy/
xfreq = np.fft.fft(body_chg)
fft_freqs = np.fft.fftfreq(len(body_chg), d=1./ds)
norm_pass = cuttoff_freq/(ds/2)
norm_stop = 1.5*norm_pass
(N, Wn) = scipy.signal.buttord(wp=norm_pass, ws=norm_stop, gpass=2, gstop=30, analog=0)
(b, a) = scipy.signal.butter(N, Wn, btype='low', analog=0, output='ba')
body_chg2 = scipy.signal.lfilter(b, a, body_chg)
np.savetxt('body.txt',body_chg2)
## let's make a movie of the FDM!
sp.Popen("ffmpeg -r 6 -i temp/diff%d.png -vcodec mpeg4 -y movie.mp4")
