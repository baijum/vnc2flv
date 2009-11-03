#!/usr/bin/env python
##
##  flvdump.py - dump the raw contents of a FLV file.
##
##  Copyright (c) 2009 by Yusuke Shinyama
##

import sys, os
from vnc2flv.flv import FLVParser, getvalue
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO
from struct import unpack, error


##  flvdump
##
RATE = (5500, 11025, 22050, 44100)
ATYPE = { 0:'PCM-p', 1:'ADPCM', 2:'MP3', 3:'PCM-l', 4:'Nel16', 5:'Nel8', 6:'Nelly',
          7:'GAPCM', 8:'GMPCM', 10:'AAC', 14:'MP3-8', 15:'Dev' }
FTYPE = { 1:'key', 2:'inter', 3:'disposable', 4:'genkey', 5:'command' }
CODEC = { 1:'JPEG', 2:'H.263', 3:'Scr', 4:'VP6', 5:'VP6A', 6:'Scrv2', 7:'AVC' }
def flvdump(fname, verbose=0, debug=0):
  fin = file(fname, 'rb')
  parser = FLVParser(fin, debug=debug)
  timestamp = 0
  other = video = audio = 0
  for (i, (tag, length, timestamp, offset)) in enumerate(parser):
    data = parser.get_data(i)
    if tag == 8:
      # Audio tag
      flags = ord(data[0])
      atype = ATYPE.get((flags & 0xf0) >> 4, '?')
      rate = RATE[(flags & 0x0c) >> 2]
      if flags & 2:
        samplesize = 16
      else:
        samplesize = 8
      if flags & 1:
        ch = 'stereo'
      else:
        ch = 'mono'
      audio += 1
      if 1 <= verbose:
        print ('%08d: audio: %s, rate=%d, %dbit, %s (%d bytes)' %
               (timestamp, atype, rate, samplesize, ch, length))
    elif tag == 9:
      # Video tag
      ftype = FTYPE.get(ord(data[0]) >> 4, '?')
      fp = StringIO(data)
      codec = ord(fp.read(1)) & 0xf
      cname = CODEC.get(codec, '?')
      video += 1
      if 1 <= verbose:
        if codec == 3:
          x = ord(fp.read(1))
          y = ord(fp.read(1))
          blockwidth = ((x >> 4)+1) * 16
          imagewidth = (x & 0xf) << 8 | y
          x = ord(fp.read(1))
          y = ord(fp.read(1))
          blockheight = ((x >> 4)+1) * 16
          imageheight = (x & 0xf) << 8 | y
          print ('%08d: video: %s/%s %dx%d (block:%dx%d) (%d bytes)' %
                 (timestamp, cname, ftype, imagewidth, imageheight,
                  blockwidth, blockheight, length))
          if 2 <= verbose:
            r = []
            for y in xrange((imageheight + blockheight-1)/blockheight):
              for x in xrange((imagewidth + blockwidth-1)/blockwidth):
                (n,) = unpack('>H', fp.read(2))
                fp.read(n)
                r.append(n)
            print ' ',r
        else:
          print '%08d: video: %s/%s (%d bytes)' % (timestamp, cname, ftype, length)
    elif tag == 18:
      # Data tag
      print '%08d: data (%d bytes)' % (timestamp, length)
      if 1 <= verbose:
        (k,v) = parser.parse_metadata(data)
        print '  %s: %r' % (k,v)
    else:
      other += 1
      if 1 <= verbose:
        print ('%08d: tag %d (%d bytes)' % (timestamp, tag, length))
    if 2 <= verbose:
      N = 16
      for i in xrange(0, len(data), N):
        line = data[i:i+N]
        print '  %s: %r' % (' '.join( '%02x' % ord(c) for c in line ), line)
  parser.close()
  print 'time=%.3f, video: %d, audio: %d, other: %d' % (timestamp*.001, video, audio, other)
  return


# main
def main(argv):
  import getopt, vnc2flv
  def usage():
    print argv[0], vnc2flv.__version__
    print ('usage: %s [-d] [-q] [-v] movie.flv' % argv[0])
    return 100
  try:
    (opts, args) = getopt.getopt(argv[1:], 'dvq')
  except getopt.GetoptError:
    return usage()
  debug = 0
  verbose = 1
  for (k, v) in opts:
    if k == '-d': debug += 1
    elif k == '-v': verbose += 1
    elif k == '-q': verbose -= 1
  if not args: return usage()
  for fname in args:
    flvdump(fname, verbose=verbose, debug=debug)
  return

if __name__ == "__main__": sys.exit(main(sys.argv))
