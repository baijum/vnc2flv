-------
vnc2flv
-------

:Date: |today|

Desktop Screen Recorder for UNIX, Linux, Windows or Mac.

`Homepage`_   `Recent Changes`_

- `What's It?`_
- `Download`_
- `How to Install`_
- `How to Use`_
- `Adding Audio`_
- `Embedding Movie`_
- `Changes`_
- `Related Links`_
- `Terms and Conditions`_

**Download:**
http://pypi.python.org/pypi/vnc2flv


**Discussion:** (for questions and comments, post here)
https://groups.google.com/forum/#!forum/vnc2flv-users


**View the source:**
https://github.com/baijum/vnc2flv


What's It?
----------

Vnc2flv is a cross-platform screen recording tool for UNIX, Windows or Mac.
It captures a VNC desktop session (either your own screen or a remote
computer) and saves as a Flash Video (FLV) file.

(Vnc2flv is a rewrite of its predecessor, vnc2swf. As FLV format is more
prevalent today, vnc2flv is specialized for FLV format and aims at a simpler
and more lightweight functionality.)

**Demo:** (created with vnc2flv itself)

.. raw:: html

  <object width="425" height="344"><param name="movie" value="http://www.youtube.com/v/DcijI6EagYI&hl=en&fs=1&"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/DcijI6EagYI&hl=en&fs=1&" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="425" height="344"></embed></object>


How to Install
--------------

1.  First of all, you have to have the `x11vnc`_ server running on your
    screen. This program captures the screen sends it to other processes. See
    also a list of `other VNC servers`_.
2.  Install `Python`_ 2.4 or newer.
3.  Download and extract the `vnc2flv source distribution
    <http://pypi.python.org/pypi/vnc2flv>`_.
4.  Run ``setup.py`` to install:

::

  python setup.py install


Installing for Windows
~~~~~~~~~~~~~~~~~~~~~~

Here is an additional instruction for Windows:

1.  Install `TightVNC`_ 1.3.10 or newer.
2.  Install `MinGW`_ 5.1.4 or newer.
3.  Do the following instead:

::

  python setup.py build -c mingw32 install


How to Use
----------

vnc2flv comes with several programs:

- `flvrec.py`_ (main recording tool)
- `flvcat.py`_ (for editing)
- `flvaddmp3.py`_ (for adding mp3 audio)
- `flvsplit.py`_ (for splitting a movie into shorter clips)
- `flvdump.py`_ (for debugging use)
- `recordwin.sh`_ (all-in-one script)


flvrec.py
~~~~~~~~~

``flvrec.py`` is the main recording program. It connects to a specified VNC
server and immediately starts recording. It stops when it receives a SIGINT
(or Ctrl-C is pressed). You need to have a VNC server running on the target
machine in advance.

The generated file is playable via either desktop programs like ffmpeg, VLC
or mplayer, or other online Flash-based players.

Syntax::

 flvrec.py [options] [host[:display]]

**or**

::

 flvrec.py [options] [host [port]]


Examples::

  $ x11vnc -quiet -localhost -viewonly -nopw -bg
  (start up a vnc server)
  
  The VNC desktop is:      localhost:0
  PORT=5900
  
  ******************************************************************************
  Have you tried the x11vnc '-ncache' VNC client-side pixel caching feature yet?
  
  The scheme stores pixel data offscreen on the VNC viewer side for faster
  retrieval.  It should work with any VNC viewer.  Try it by running:
  
      x11vnc -ncache 10 ...
  
  more info: http://www.karlrunge.com/x11vnc/#faq-client-caching
  
  $ flvrec.py localhost:0
  (Record a local desktop)
  
  $ flvrec.py -C 640x480+0-0 remotehost:0
  (Record a remote desktop with a 640x480 window at the bottom left of the screen.)
  
  $ flvrec.py -S 'arecord sample.wav'
  (Record a local desktop and capture audio input simultaneously using the ALSA recording utility)

Options:


.. cmdoption:: -o filename

    Specifies the output file name. By default, the output
    file is given with a unique name.

.. cmdoption:: -r fps

    Specifies the number of frames per second. (default: 15)

.. cmdoption:: -K keyframe

    Specifies the rate of key frames that is inserted in every
    this number of frames. (default: every 150 frames)

.. cmdoption:: -P pwdfile

    Specifies the password file for a vnc session.

.. cmdoption:: -N

    Suppress the appearance of mouse pointer in the video.

.. cmdoption:: -e encoding,encoding,...

    Specifies the vnc encoding methods. (default: raw)

.. cmdoption:: -B blocksize

    Specifies the block size. (default: 32)

.. cmdoption:: -C WxH{+|-}X{+|-}Y

    Specifies the clipping. (default: entire screen)

.. cmdoption:: -S commandline

    Starts a child process immediately after the recording
    is started. This process runs parallely with flvrec.py and can be used for
    recording audio. When the recording is stopped, a SIGINT is sent to the
    subprocess.

.. cmdoption:: -d

    Increases the debug level.


flvcat.py
~~~~~~~~~

``flvcat.py`` is a simplistic editing program for a FLV movie. It supports
concatenating multiple movies, clipping a movie's frame size, re-sampling a
movie into a smaller size with auto-panning, etc.
Syntax:

::

  flvcat.py [options] src1[:ranges1] src2[:ranges2] ... output

For each movie file, you can clip the parts of the movie to add by specifying
its ranges. *Ranges* is comma-separated, hyphenated list of milliseconds. For
example,

::

  out.flv:10000-20000

means a 10-second clip from movie ``out.flv`` (0:10-0:20). Specifying only
one end of the range is also supported::

  out.flv:10000-

means the entire movie except the first 10 seconds. When *ranges* are
omitted, the whole movie is used.

Examples::

  $ flvcat.py movie1.flv movie2.flv output.flv
  (Concatenate movie1.flv and movie2.flv and save it as output.flv)

  $ flvcat.py -W 640x480 movie1.flv output.flv
  (Resize the movie1.flv with auto-panning with its window size 640x480
   and save it as output.flv)*

  $ flvcat.py movie1.flv:15000-30000 output.flv
  (Clip the part of movie1.flv from 0:15 to 0:30 and save it as
  output.flv)

  $ flvcat.py movie1.flv:2500- output.flv
  (Chop the first 2.5 seconds off and save it as output.flv)


Options:

.. cmdoption:: -r fps

    Specifies the number of frames per second. (default: 15)

.. cmdoption:: -K keyframe

    Specifies the rate of key frames that is inserted in every
    this number of frames. (default: every 150 frames)

.. cmdoption:: -B blocksize

    Specifies the block size. (default: 32)

.. cmdoption:: -C WxH{+|-}X{+|-}Y

    Specifies the clipping. (default: entire frame)

.. cmdoption:: -W WxH

    Specifies the window size for auto panning. Auto panning tracks the
    changes in the screen and tries to focus on the active part of the screen.
    This helps reducing the movie screen size. (default: no auto panning)

.. cmdoption:: -S speed

    Specifies the speed of auto panning. (default: 60 frames)

.. cmdoption:: -f

    Forces overwriting the output file.


flvaddmp3.py
~~~~~~~~~~~~

Add mp3 audio files to a movie.

Syntax::

  flvaddmp3.py [options] src mp3file1[:ranges] mp3file2[:ranges] ... output


Options:

.. cmdoption:: -f

    Forces overwriting the output file.


flvsplit.py
~~~~~~~~~~~

Split a movie file into shorter clips. This can be used to chop movies into
several chunks in order to fit each of them within the length limitation in
several movie sites (e.g. YouTube).

Syntax::

  flvsplit.py [options] src dstbase


Options::

.. cmdoption:: -f

    Forces overwriting the output file.

.. cmdoption:: -r fps

    Specifies the number of frames per second. (default: 15)

.. cmdoption:: -K keyframe

    Specifies the rate of key frames that is inserted in every this number of frames.
    (default: every 150 frames)

.. cmdoption:: -B blocksize

    Specifies the block size. (default: 32)

.. cmdoption:: -D duration

    Specifies the maximum movie length in seconds. (default: 600)

.. cmdoption:: -P overlap

    Specifies the length of overlapping parts
    in consecutive clips in seconds. (default: 5)


flvdump.py
~~~~~~~~~~

This program dumps the contents of a FLV file. This is used solely for
debugging purposes.

Syntax::

  flvdump.py [options] flvfile


recordwin.sh
~~~~~~~~~~~~

This program is a shell script that launches a VNC server (``x11vnc``), the
screen recorder (``flvrec.py``) and a voice recorder (``arecord``), and
combines the output files into a single playable FLV file. A recording area
in the screen can be either an entire desktop or a single window. In the
latter case, a target window can be chosen by giving the window ID or window
name, or simply click a window after a prompt cursor appears. When a filename
is unspecified, a generated movie is automatically given a unique filename.
Syntax:

::

 recordwin.sh [options] [filename]


Options:

.. cmdoption:: -all

    Instructs to record an entire desktop.

.. cmdoption:: -name window_name

    Specifies the title of the target window.

.. cmdoption:: -id window_id

    Specifies the Window ID of the target window.

.. cmdoption:: -display display_name

    Specifies the name of the X11 screen where a VNC server is to be started.

Adding Audio
------------

`flvrec.py`_ can designate a child process to record audio during
recording. By giving ``-S`` option, the specified command line is executed
when the recording is started. The child process can capture audio input and
encode it as an appropriate format. The process is terminated when the
recording is stopped. To put it onto an FLV movie, the audio needs to be
encoded as MP3 format. After the recording is finished, the user can use the
`flvaddmp3.py`_ command to combine the movie and audio output.

.. note::

    The audio sampling rate must be one of the following: 5500Hz,
    11025Hz, 22050Hz, or 44100Hz.

1. Record the screen and audio simultaneously

::

  $ flvrec.py -S 'arecord -f cd out.wav'

2. Convert the WAV file into MP3

::

  $ lame out.wav out.mp3

3. Add the MP3 file to the movie

::

  $ flvaddmp3 out200908122312.flv out.mp3 final.flv


**or**

Just do this::

  $ recordwin.sh*


`recordwin.sh`_ is a script for making these tasks easy. It launches a
VNC server and automatically does the things described above.


Embedding Movie
---------------

Currently the following free/opensource embeddable movie players are known to
work with vnc2flv:

- `JW FLV Player`_
- `OS FLV`_
- `FLV Player`_


Changes
-------

- 2010/01/22: flvsplit.py added.
- 2009/11/14: SIGINT bug fixed.
- 2009/10/25: FLV metadata support.
- 2009/08/30: recordwin.sh script is added.
- 2009/08/24: Improved documentation.
- 2009/08/17: Synchronized audio recording support is added.
- 2009/08/02: various bugfixes. Command name changed: mp3add.py ->
  flvaddmp3.py.
- 2009/07/22: flvcat.py added.
- 2009/07/04: rfb protocol handling modified. (hopefully better auto-
  scrolling)
- 2009/07/02: mp3add.py and flvdump.py added.
- 2009/06/28: Initial release.


Related Links
-------------

-   VNC servers: `RealVNC`_, `TightVNC`_, `UltraVNC`_, `x11vnc`_
-   FLV players (desktop): `FFMpeg`_, `MPlayer`_, `VLC media player`_
-   FLV players (flash): `JW FLV Player`_, `OS FLV`_, `FLV Player`_
-   Flash players: `Adobe Flash Player`_, `GNU Gnash`_


Terms and Conditions
--------------------

Copyright (c) 2009 Yusuke Shinyama <yusuke at cs dot nyu dot edu>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

.. _Homepage: http://www.unixuser.org/~euske/python/vnc2flv/index.html
.. _Recent Changes: #changes
.. _What's It?: #intro
.. _Download: #source
.. _How to Install: #install
.. _How to Use: #usage
.. _Adding Audio: #addaudio
.. _Embedding Movie: #embed
.. _Related Links: #related
.. _Terms and Conditions: #license
.. _ http://pypi.python.org/pypi/vnc2flv/ :
    http://pypi.python.org/pypi/vnc2flv/
.. _ http://groups.google.com/group/vnc2flv-users/ :
    http://groups.google.com/group/vnc2flv-users/
.. _ http://code.google.com/p/vnc2flv/source/browse/trunk/vnc2flv :
    http://code.google.com/p/vnc2flv/source/browse/trunk/vnc2flv
.. _x11vnc: http://www.karlrunge.com/x11vnc/
.. _other VNC servers: #server
.. _Python: http://www.python.org/download/
.. _TightVNC: http://www.tightvnc.com/
.. _MinGW: http://www.mingw.org/
.. _flvrec.py: #flvrec.py
.. _flvcat.py: #flvcat.py
.. _flvaddmp3.py: #flvaddmp3.py
.. _flvsplit.py: #flvsplit.py
.. _flvdump.py: #flvdump.py
.. _recordwin.sh: #recordwin.sh
.. _JW FLV Player: http://www.longtailvideo.com/players/jw-flv-player/
.. _OS FLV: http://www.osflv.com/
.. _FLV Player: http://flv-player.net/
.. _RealVNC: http://www.realvnc.com/
.. _UltraVNC: http://ultravnc.sourceforge.net/
.. _FFMpeg: http://ffmpeg.org/
.. _MPlayer: http://www.mplayerhq.hu/
.. _VLC media player: http://www.videolan.org/vlc/
.. _Adobe Flash Player: http://www.adobe.com/products/flashplayer/
.. _GNU Gnash: http://www.gnashdev.org/
