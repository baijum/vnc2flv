#!/usr/bin/env python
##
##  audio.py - mp3 file handling
##
##  Copyright (c) 2009 by Yusuke Shinyama
##

import sys
from struct import pack, unpack
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


##  MP3Parser
##
BIT_RATE = {
  (1,1): (0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 0),
  (1,2): (0, 32, 48, 56,  64,  80,  96, 112, 128, 160, 192, 224, 256, 320, 384, 0),
  (1,3): (0, 32, 40, 48,  56,  64,  80,  96, 112, 128, 160, 192, 224, 256, 320, 0),
  (2,1): (0, 32, 48, 56,  64,  80,  96, 112, 128, 160, 144, 176, 192, 224, 256, 0),
  (2,2): (0,  8, 16, 24,  32,  40,  48,  56,  64,  80,  96, 112, 128, 144, 160, 0),
  (2,3): (0,  8, 16, 24,  32,  40,  48,  56,  64,  80,  96, 112, 128, 144, 160, 0),
  }

SAMPLE_RATE = {
  3: (44100, 48000, 32000), # V1
  2: (22050, 24000, 16000), # V2
  0: (11025, 12000,  8000), # V2.5
  }

FLV_RATE = { 5500:0x00, 11025:0x04, 22050:0x0a, 44100:0x0c }

def parse_mp3(fp, debug=0):
    if isinstance(fp, str):
        fp = StringIO(fp)
    while 1:
        x = fp.read(4)
        if len(x) < 4: break
        if x.startswith('TAG'):
            # TAG - ignored
            data = x[3]+fp.read(128-4)
            if debug: print >>sys.stderr, 'TAG', repr(data)
            continue
        elif x.startswith('ID3'):
            # ID3 - ignored
            id3version = x[3]+fp.read(1)
            flags = ord(fp.read(1))
            s = [ ord(c) & 0x7f for c in fp.read(4) ]
            size = (s[0]<<21) | (s[1]<<14) | (s[2]<<7) | s[3]
            data = fp.read(size)
            if debug: print >>sys.stderr, 'ID3', repr(data)
            continue
        h = unpack('>L', x)[0]
        # All sync bits (b31-21) are set?
        if (h & 0xffe00000L) != 0xffe00000L: continue
        # MPEG Audio Version ID (0:v2.5, 2:mpeg2, 3:mpeg1)
        version = (h & 0x00180000L) >> 19
        if version == 1: continue
        # Layer (1:layer1, 2:layer2, 3:mp3)
        layer = 4 - ((h & 0x00060000L) >> 17)
        if layer == 4: continue
        # Protection (1: protected by CRC)
        protected = not (h & 0x00010000L)
        # Bitrate index
        b = (h & 0xf000) >> 12
        if b == 0 or b == 15: continue
        # Frequency index
        s = (h & 0x0c00) >> 10
        if s == 3: continue
        # Bitrate
        if version == 3:                      # V1
            bit_rate = BIT_RATE[(1,layer)][b]
        else:                                 # V2 or V2.5
            bit_rate = BIT_RATE[(2,layer)][b]
        # Sampling rate
        sample_rate = SAMPLE_RATE[version][s]
        # Number of samples
        nsamples = 1152
        if sample_rate <= 24000:
            nsamples = 576
        # Padding (1: padded)
        pad = (h & 0x0200) >> 9
        # Channels (0:stereo, 1:joint, 2:dual, 3:mono)
        channels = (h & 0xc0) >> 6
        # Joint stereo extension
        joint = (h & 0x30) >> 4
        # Copyright (1: copyrighted)
        copyrighted = bool(h & 8)
        # Original (1: original)
        original = bool(h & 4)
        # Enphasis (0:none, 1:50/15ms, 2:reserved, 3:CCIT.J17)
        emphasis = h & 3
        # Frame size
        if version == 3:
            framesize = 144000 * bit_rate / sample_rate + pad
        else:
            framesize = 72000 * bit_rate / sample_rate + pad
        if protected:
            # skip 16bit CRC
            fp.read(2)
        if debug:
            print >>sys.stderr, 'Frame: bit_rate=%dk, sample_rate=%d, framesize=%d' % \
                  (bit_rate, sample_rate, framesize)
        data = x+fp.read(framesize-4)
        yield (nsamples, sample_rate, channels, data)
    return


##  AudioBuffer
##
class AudioBuffer(object):

    def __init__(self, debug=0):
        self.debug = debug
        self.frames = []
        self.rate = None
        self.totalsamples = 0
        return

    def __repr__(self):
        return '<AudioBuffer: frames=%d, samples=%d, rate=%s>' % (len(self.frames), self.totalsamples, self.rate)

    def load(self, fp, timeranges=None):
        n = 0
        for (nsamples, rate, channels, data) in parse_mp3(fp):
            if self.rate == None:
                self.rate = rate
            elif self.rate != rate:
                raise ValueError('bitrate changed!')
            t = n*1000/self.rate
            n += nsamples
            if timeranges:
                if timeranges.seekandmap(t) < 0: continue
            stereo = (channels == 0 or channels == 1)
            self.frames.append((self.totalsamples, nsamples, rate, stereo, data))
            self.totalsamples += nsamples
        return

    def get(self, start=0, end=sys.maxint):
        if not self.rate: return
        cursamples = int(self.rate * start / 1000.0)
        i0 = 0
        i1 = len(self.frames)
        while i0 < i1:
            i = (i0+i1)/2
            (ns,_,_,_,_) = self.frames[i]
            if cursamples == ns:
                (i0,i1) = (i,i+1)
                break
            elif cursamples < ns:
                i1 = i
            else:
                i0 = i+1
        curframe = i0
        if curframe == len(self.frames):
            cursamples = self.totalsamples
        else:
            (cursamples, _,_,_,_) = self.frames[curframe]
        while curframe < len(self.frames):
            t = int(cursamples*1000.0 / self.rate + .5)
            if end <= t: break
            (_, nsamples, rate, stereo, data) = self.frames[curframe]
            curframe += 1
            cursamples += nsamples
            yield (t, nsamples, rate, stereo, data)
        return

    def put(self, writer, start=0, end=sys.maxint, timestamp=0):
        if not self.rate: return 0
        totalsamples = 0
        for (t, nsamples, rate, stereo, data) in self.get(start, end):
            flags = (0x22 | FLV_RATE[rate])
            if stereo:
                flags |= 1
            totalsamples += nsamples
            writer.write_audio_frame(t-start+timestamp, chr(flags)+data)
        return int(totalsamples*1000.0 / self.rate + .5)


if __name__ == "__main__":
    fp = file(sys.argv[1], 'rb')
    for (nsamples,rate,channels,data) in parse_mp3(fp):
        print (nsamples,rate,channels, len(data))
    fp.close()
