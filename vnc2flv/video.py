#!/usr/bin/env python
##
##  video.py - recoding VNC to FLV.
##
##  Copyright (c) 2009-2010 by Yusuke Shinyama
##

import sys, zlib, re
from struct import pack, unpack
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from flvscreen import FlvScreen


##  Utilities
##
def str2clip(s):
    m = re.match(r'^(\d+)x(\d+)([\-\+])(\d+)([\-\+])(\d+)$', s)
    if not m:
        raise ValueError('Invalid clipping spec: %r' % s)
    return ((m.group(3), int(m.group(4))),
            (m.group(5), int(m.group(6))),
            int(m.group(1)), int(m.group(2)))

def str2size(s):
    m = re.match(r'^(\d+)x(\d+)$', s)
    if not m:
        raise ValueError('Invalid size spec: %r' % s)
    f = map(int, m.groups())
    return (f[0],f[1])

class MultipleRange(object):

    def __init__(self, s):
        self.ranges = []
        if isinstance(s, basestring):
            t = 0
            for x in s.split(','):
                m = re.match(r'(\d+)?-(\d+)?', x)
                if not m:
                    raise ValueError('Invalid range spec: %r' % x)
                if m.group(1):
                    i1 = int(m.group(1))
                else:
                    i1 = 0
                if m.group(2):
                    i2 = int(m.group(2))
                else:
                    i2 = sys.maxint
                self.ranges.append((t,i1,i2))
                t += (i2-i1)
        elif isinstance(s, list):
            t = 0
            for (i1,i2) in s:
                self.ranges.append((t,i1,i2))
                t += (i2-i1)
        self.ranges.sort()
        self.pos = 0
        return

    def __iter__(self):
        return iter(self.ranges)

    def get_total(self, tmax):
        t = 0
        for (_,i1,i2) in self.ranges:
            if i2 == sys.maxint:
                i2 = tmax
            t += (i2-i1)
        return t

    def seekandmap(self, i):
        while self.pos < len(self.ranges):
            (t,i1,i2) = self.ranges[self.pos]
            if i < i1: return -1
            if i <= i2: return (i-i1+t)
            self.pos += 1
        return -1


##  VideoSink
##
class VideoSink(object):

    def __init__(self, clipping=None, debug=0):
        self.debug = debug
        self.clipping = clipping
        self.initialized = False
        return

    def init_screen(self, width, height, name=None):
        if self.debug:
            print >>sys.stderr, 'init_screen: %dx%d, name=%r' % (width, height, name)
        if self.clipping:
            ((xs,x), (ys,y), w, h) = self.clipping
            if xs == '-':
                (x,width) = (width-w-x,w)
            else:
                (x,width) = (x,w)
            if ys == '-':
                (y,height) = (height-h-x,h)
            else:
                (y,height) = (y,h)
        else:
            (x, y) = (0, 0)
        self.initialized = True
        return (x, y, width, height)

    # data is given as ARGB
    def convert_pixels(self, data):
        return data
    def convert_color1(self, data):
        return unpack('BBBx', data)

    def update_cursor_image(self, width, height, data):
        if self.debug:
            print >>sys.stderr, 'update_cursor_image: %dx%d' % (width, height)
        return

    def update_cursor_pos(self, x, y):
        if self.debug:
            print >>sys.stderr, 'update_cursor_pos: (%d,%d)' % (x,y)
        return

    def update_screen_rgbabits(self, (x, y), (width, height), data):
        if self.debug:
            print >>sys.stderr, 'update_screen_rgbabits: %dx%d at (%d,%d)' % (width,height,x,y)
        return

    def update_screen_solidrect(self, (x, y), (w, h), data):
        if self.debug:
            print >>sys.stderr, 'update_screen_solidrect: %dx%d at (%d,%d), color=%r' % (width,height,x,y, color)
        return

    def flush(self, t):
        if self.debug:
            print >>sys.stderr, 'flush', t
        return

    def close(self):
        if self.debug:
            print >>sys.stderr, 'close'
        return


##  FLVVideoSink
##
class FLVVideoSink(VideoSink):

    def __init__(self, writer, blocksize=32, framerate=15, keyframe=0,
                 clipping=None, panwindow=None, panspeed=0, debug=0):
        VideoSink.__init__(self, clipping=clipping, debug=debug)
        self.writer = writer
        self.blocksize = blocksize
        self.framerate = framerate
        self.keyframe = keyframe
        self.panwindow = panwindow
        self.panspeed = panspeed
        self.screen = None
        self.screenpos = (0,0)
        self.screensize = None
        self.windowpos = (0,0)
        self.windowsize = None
        self.curframe = 0
        self.changes = []
        return

    def init_screen(self, width, height, name=None):
        (x,y, width, height) = VideoSink.init_screen(self, width, height, name=name)
        bw = (width+self.blocksize-1) / self.blocksize
        bh = (height+self.blocksize-1) / self.blocksize
        self.screenpos = (x,y)
        self.screensize = (bw,bh)
        self.screen = FlvScreen(self.blocksize, bw, bh)
        if self.panwindow:
            (w, h) = self.panwindow
            self.windowsize = ((w+self.blocksize-1) / self.blocksize,
                               (h+self.blocksize-1) / self.blocksize)
        else:
            self.windowsize = (bw, bh)
        if self.debug:
            print >>sys.stderr, 'start: %d,%d (%dx%d)' % (x, y, width, height)
        self.writer.set_screen_size(width, height)
        return (x, y, width, height)

    def update_screen_rgbabits(self, (x, y), (w, h), data):
        (x0,y0) = self.screenpos
        self.screen.blit_rgba(x-x0, y-y0, w, h, data)
        return

    def flush(self, t):
        # t must be >= 0
        if not self.screen: return
        while 1:
            timestamp = self.curframe * 1000 / self.framerate
            if t < timestamp: break
            self.writer.write_video_frame(timestamp, self.get_update_frame())
            self.curframe += 1
        return

    # write SCREENVIDEOPACKET tag
    def get_update_frame(self):
        changes = self.screen.changed()
        self.screen.reset()
        (bw,bh) = self.windowsize
        (bx,by) = self.do_autopan(self.windowpos, changes)
        key = ((bx,by) != self.windowpos or
               (self.keyframe and (self.curframe % self.keyframe) == 0))
        if key:
            # update the entire screen if necessary.
            self.windowpos = (bx,by)
            changes = set( (bx+x,by+y) for y in xrange(bh) for x in xrange(bw) )
        else:
            changes = set(changes)
        if self.debug:
            print >>sys.stderr, 'update(%d): changes=%r' % (self.curframe, len(changes)), sorted(changes)
        flags = 3  # screenvideo codec
        if key:
            flags |= 0x10
        else:
            flags |= 0x20
        data = chr(flags)
        w = bw * self.blocksize
        h = bh * self.blocksize
        data += chr((self.blocksize/16-1) << 4 | w >> 8) + chr(w & 0xff)
        data += chr((self.blocksize/16-1) << 4 | h >> 8) + chr(h & 0xff)
        n = 0
        for y in xrange(bh, 0, -1):
            y = by+y-1
            for x in xrange(bw):
                x += bx
                if (x,y) in changes:
                    # changed block
                    block = zlib.compress(self.screen.get(x,y))
                    data += pack('>H', len(block)) + block
                else:
                    # unchanged block
                    data += pack('>H', 0)
        return data

    # do paning.
    def do_autopan(self, (wx,wy), changes):
        if changes:
            r = (min( x for (x,y) in changes ),
                 min( y for (x,y) in changes ),
                 max( x for (x,y) in changes )+1,
                 max( y for (x,y) in changes )+1)
            self.changes.append(r)
        elif self.changes:
            self.changes.append(self.changes[-1])
        self.changes = self.changes[-self.panspeed:]
        cx0 = sum( x0 for (x0,y0,x1,y1) in self.changes ) / len(self.changes)
        cy0 = sum( y0 for (x0,y0,x1,y1) in self.changes ) / len(self.changes)
        cx1 = sum( x1 for (x0,y0,x1,y1) in self.changes ) / len(self.changes)
        cy1 = sum( y1 for (x0,y0,x1,y1) in self.changes ) / len(self.changes)
        (w,h) = self.windowsize
        (bw,bh) = self.screensize
        if w < cx1-cx0:
            wx = min(max(0, (cx0+cx1-w)/2), bw-w)
        elif cx0 < wx:
            wx = cx0
        elif wx < cx1-w:
            wx = cx1-w
        if h <= cy1-cy0:
            wy = min(max(0, (cy0+cy1-h)/2), bh-h)
        elif cy0 < wy:
            wy = cy0
        elif wy < cy1-h:
            wy = cy1-h
        return (wx,wy)


##  FLVMovieProcessor
##
class FLVMovieProcessor(object):

    def __init__(self, writer=None, debug=0):
        self.debug = debug
        self.writer = writer
        self.basetime = 0
        return

    def process_audio_tag(self, audiosink, data):
        flags = ord(data[0])
        # must be mp3 packet
        if (flags & 0xf0) != 0x20: return
        samplerate = (flags & 0x0c) >> 2
        samplerate = [5500,11025,22050,44100][samplerate]
        samplesize = 8
        if flags & 2:
            samplesize = 16
        samplestereo = flags & 1
        audiosink.load(data[1:])
        return

    def process_video_tag(self, videosink, data):
        import flvscreen, zlib
        (frametype, codecid) = ord(data[0]) >> 4, ord(data[0]) & 0xf
        # must be ScreenVideo
        if codecid != 3: return
        (blockwidth, imagewidth) = ord(data[1]) >> 4, (ord(data[1]) & 0xf) << 8 | ord(data[2])
        (blockheight, imageheight) = ord(data[3]) >> 4, (ord(data[3]) & 0xf) << 8 | ord(data[4])
        blockwidth = (blockwidth+1)*16
        blockheight = (blockheight+1)*16
        hblocks = (imagewidth+blockwidth-1)/blockwidth
        vblocks = (imageheight+blockheight-1)/blockheight
        if not videosink.initialized:
            videosink.init_screen(imagewidth, imageheight)
        fp = StringIO(data[5:])
        changed = []
        for y in xrange(vblocks):
            for x in xrange(hblocks):
                (length,) = unpack('>H', fp.read(2))
                if not length: continue
                data = fp.read(length)
                x0 = x*blockwidth
                y0 = imageheight - (y+1)*blockheight
                w = min(blockwidth, imagewidth-x0)
                h = blockheight
                if y0 < 0:
                    h += y0
                    y0 = 0
                data = zlib.decompress(data)
                data = flvscreen.flv2rgba(w, h, data)
                changed.append((x,vblocks-y-1))
                videosink.update_screen_rgbabits((x0, y0), (w, h), data)
        return

    def process_flv(self, parser, audiosink=None, videosink=None, ranges=None):
        timestamp = 0
        for (i, (tag, _, timestamp, _, keyframe)) in enumerate(parser):
            data = parser.get_data(i)
            if tag == 9:
                if videosink:
                    self.process_video_tag(videosink, data)
            elif tag == 8:
                if audiosink:
                    self.process_audio_tag(audiosink, data)
            else:
                self.writer.write_other_data(tag, data)
                continue
            if ranges:
                timestamp = ranges.seekandmap(timestamp)
                if timestamp < 0: continue
            if videosink:
                videosink.flush(timestamp)
        if ranges:
            timestamp = ranges.get_total(timestamp)
        if audiosink:
            if ranges:
                for (t,s,e) in ranges:
                    audiosink.put(self.writer, s, e, t)
            else:
                audiosink.put(self.writer)
        if videosink:
            videosink.flush(timestamp)
        self.writer.flush()
        self.writer.add_basetime(timestamp)
        return


# main
if __name__ == '__main__':
    from flv import FLVWriter
    from rfb import RFBNetworkClient
    fp = file('out.flv', 'wb')
    writer = FLVWriter(fp)
    sink = FLVVideoSink(writer, debug=1)
    client = RFBNetworkClient('127.0.0.1', 5900, sink)
    client.open()
    try:
        while 1:
            client.idle()
    except KeyboardInterrupt:
        pass
    client.close()
    writer.close()
    fp.close()
