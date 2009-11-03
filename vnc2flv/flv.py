#!/usr/bin/env python
##
##  flv.py - reading/writing FLV file format.
##
##  Copyright (c) 2009 by Yusuke Shinyama
##

import sys
from struct import pack, unpack
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


# return the number of required bits for x.
def needbits1(x, signed=False):
  if x == 0:
    return 0
  if signed:
    n = 1
    if x < 0:
      x = -x-1
  else:
    n = 0
    assert 0 < x
  while 1:
    n += 1
    x >>= 1
    if x == 0: break
  return n

def needbits(args, signed=False):
  return max([ needbits1(x, signed) for x in args ])
# assert needbits1(0,0) == 0
# assert needbits1(0,1) == 0
# assert needbits1(1,0) == 1
# assert needbits1(1,1) == 2
# assert needbits1(2,0) == 2
# assert needbits1(-2,1) == 2
# assert needbits1(-3,1) == 3
# assert needbits1(127,0) == 7
# assert needbits1(127,1) == 8
# assert needbits1(128,0) == 8
# assert needbits1(-128,1) == 8
# assert needbits1(-129,1) == 9
# assert needbits1(-6380,1) == 14

# get value
def getvalue(fp):
  t = fp.read(1)
  if not t:
    raise EOFError
  elif t == '\x00':
    (n,) = unpack('>d', fp.read(8))
    return n
  elif t == '\x01':
    return bool(ord(fp.read(1)))
  elif t == '\x02' or t == '\x04':
    (n,) = unpack('>H', fp.read(2))
    return fp.read(n)
  elif t == '\x03':
    d = {}
    try:
      while 1:
        (n,) = unpack('>H', fp.read(2))
        if n == 0:
          assert fp.read(1) == '\x09'
          break
        k = fp.read(n)
        v = getvalue(fp)
        d[k] = v
    except (error, EOFError):
      pass
    return d
  elif t == '\x07':
    (n,) = unpack('>H', fp.read(2))
    return n
  elif t == '\x08':
    (n,) = unpack('>L', fp.read(4))
    d = {}
    for _ in xrange(n):
      (n,) = unpack('>H', fp.read(2))
      k = fp.read(n)
      v = getvalue(fp)
      d[k] = v
    return d
  elif t == '\x0a':
    (n,) = unpack('>L', fp.read(4))
    return [ getvalue(fp) for _ in xrange(n) ]
  elif t == '\x0b':
    return fp.read(10)
  elif t == '\x0c':
    (n,) = unpack('>L', fp.read(4))
    return fp.read(n)
  else:
    return None  


##  DataParser
##
class DataParser(object):

  def __init__(self, fp, debug=0):
    self.fp = fp
    self.buff = 0
    self.bpos = 8
    self.debug = debug
    return
    
  def close(self):
    return

  # fixed bytes read
  
  def read(self, n):
    x = self.fp.read(n)
    if len(x) != n:
      raise EOFError
    return x
  
  def readui8(self):
    return ord(self.read(1))
  def readsi8(self):
    return unpack('<b', self.read(1))[0]
  
  def readui16(self):
    return unpack('<H', self.read(2))[0]
  def readub16(self):
    return unpack('>H', self.read(2))[0]
  def readsi16(self):
    return unpack('<h', self.read(2))[0]
  
  def readub24(self):
    return unpack('>L', '\x00'+self.read(3))[0]

  def readui32(self):
    return unpack('<L', self.read(4))[0]
  def readub32(self):
    return unpack('>L', self.read(4))[0]

  def readrgb(self):
    return ( self.readui8(), self.readui8(), self.readui8() )
  def readrgba(self):
    return ( self.readui8(), self.readui8(), self.readui8(), self.readui8() )

  # fixed bits read

  def setbuff(self, bpos=8, buff=0):
    (self.bpos, self.buff) = (bpos, buff)
    return
  
  def readbits(self, bits, signed=False):
    if bits == 0: return 0
    bits0 = bits
    v = 0
    while 1:
      r = 8-self.bpos # the number of the remaining bits we can get from the current byte.
      if bits <= r:
        # |-----8-bits-----|
        # |-bpos-|-bits-|  |
        # |      |----r----|
        v = (v<<bits) | ((self.buff>>(r-bits)) & ((1<<bits)-1))
        self.bpos += bits
        break
      else:
        # |-----8-bits-----|
        # |-bpos-|---bits----...
        # |      |----r----|
        v = (v<<r) | (self.buff & ((1<<r)-1))
        bits -= r
        self.buff = ord(self.read(1))
        self.bpos = 0
    if signed and (v>>(bits0-1)):
      v -= (1<<bits0)
    return v
  
  # variable length structure

  def readstring(self):
    s = []
    while 1:
      c = self.read(1)
      if c == '\x00': break
      s.append(c)
    return unicode(''.join(s), self.encoding)


##  DataWriter
##  A common superclass for SWFWriter and FLVWriter
##
class DataWriter(object):

  def __init__(self, fp, debug=0):
    self.fp = fp
    self.bpos = 0
    self.buff = 0
    self.fpstack = []
    self.debug = debug
    return

  def push(self):
    self.fpstack.append(self.fp)
    self.fp = StringIO()
    return

  def pop(self):
    assert self.fpstack, 'empty fpstack'
    self.fp.seek(0)
    data = self.fp.read()
    self.fp = self.fpstack.pop()
    return data

  def close(self):
    self.finishbits()
    assert not self.fpstack, 'fpstack not empty'
    return

  # fixed bytes write
  
  def write(self, *args):
    for x in args:
      self.fp.write(x)
    return

  def writeui8(self, *args):
    for x in args:
      self.fp.write(chr(x))
    return
  def writesi8(self, *args):
    for x in args:
      self.fp.write(pack('<b', x))
    return
  
  def writeui16(self, *args):
    for x in args:
      self.fp.write(pack('<H', x))
    return 
  def writeub16(self, *args):
    for x in args:
      self.fp.write(pack('>H', x))
    return 
    
  def writesi16(self, *args):
    for x in args:
      self.fp.write(pack('<h', x))
    return
  
  def writeub24(self, *args):
    for x in args:
      self.fp.write(pack('>L', x)[1:4])
    return

  def writeui32(self, *args):
    for x in args:
      self.fp.write(pack('<L', x))
    return
  def writeub32(self, *args):
    for x in args:
      self.fp.write(pack('>L', x))
    return

  def writergb(self, (r,g,b)):
    self.writeui8(r,g,b)
    return
  def writergba(self, (r,g,b,a)):
    self.writeui8(r,g,b,a)
    return

  # fixed bits write
  def writebits(self, bits, x, signed=False):
    if signed and x < 0:
      x += (1<<bits)
    assert 0 <= x and x < (1<<bits)
    while 1:
      r = 8-self.bpos # the number of the remaining bits we can add to the current byte.
      if bits <= r:
        # |-----8-bits-----|
        # |-bpos-|-bits-|  |
        # |      |----r----|
        self.buff |= x << (r-bits)
        self.bpos += bits               # <= 8
        break
      else:
        # |-----8-bits-----|
        # |-bpos-|---bits----...
        # |      |----r----|
        self.fp.write(chr(self.buff | (x >> (bits-r)))) # r < bits
        self.buff = 0
        self.bpos = 0
        bits -= r                      # cut off the upper r bits
        x &= (1<<bits)-1
    return
  
  def finishbits(self):
    if self.bpos:
      self.fp.write(chr(self.buff))
      self.buff = 0
      self.bpos = 0
    return
  
  # variable length structure
  
  def writestring(self, s):
    assert '\x00' not in s
    self.write(s)
    self.write('\x00')
    return

  def start_tag(self):
    self.push()
    return
  

##  FLVParser
##
class FLVParser(DataParser):
  
  def __init__(self, fp, debug=0):
    DataParser.__init__(self, fp, debug=debug)
    self.tags = []
    self.parse_header()
    self.parse_tags()
    return

  def parse_header(self):
    (F,L,V,ver) = self.read(4)
    assert F+L+V == 'FLV'
    self.flv_version = ord(ver)
    flags = self.readui8()
    self.has_audio = bool(flags & 4)
    self.has_video = bool(flags & 1)
    offset = self.readub32()
    if self.debug:
      print >>sys.stderr, 'Header:', (F,L,V,self.flv_version,flags)
    return

  def parse_metadata(self, data):
    fp = StringIO(data)
    (k,v) = (getvalue(fp), getvalue(fp))
    if self.debug:
      print >>sys.stderr, 'Metadata:', (k,v)
    return (k,v)

  def parse_tags(self):
    try:
      offset = self.readub32()          # always 0
      while 1:
        tag = self.readui8()
        length = self.readub24()
        timestamp = self.readub24()     # timestamp in msec.
        reserved = self.readub32()
        offset = self.fp.tell()
        self.tags.append((tag, length, timestamp, offset))
        self.fp.seek(offset + length + 4)  # skip PreviousTagSize
    except EOFError:
      pass
    if self.debug:
      print >>sys.stderr, 'Tags:', len(self.tags)
    return
  
  def dump(self):
    for (tag, length, timestamp, offset) in self.tags:
      print 'tag=%d, length=%d, timestamp=%.03f' % (tag, length, timestamp*.001)
    return

  def __len__(self):
    return len(self.tags)

  def __iter__(self):
    return iter(self.tags)

  def __getitem__(self, i):
    return self.tags[i]
    
  def get_data(self, i):
    (tag, length, timestamp, offset) = self.tags[i]
    self.fp.seek(offset)
    data = self.read(length)
    return data

  def seek(self, t):
    i0 = 0
    i1 = len(self.tags)
    while i0 < i1:
      i = (i0+i1)/2
      (tag, length, timestamp, offset) = self.tags[i]
      if timestamp == t:
        i0 = i
        break
      elif timestamp < t:
        i0 = i
      else:
        i1 = i
    return i0


##  FLVWriter
##
##  Originally contributed by Luis Fernando <lfkpoa-69@yahoo.com.br>
##
class FLVWriter(DataWriter):

  TAG_AUDIO = 8
  TAG_VIDEO = 9
  TAG_DATA = 18
  
  def __init__(self, fp, flv_version=1, has_video=True, has_audio=False, framerate=12, debug=0):
    DataWriter.__init__(self, fp, debug=debug)
    self.flv_version = flv_version
    self.has_video = has_video
    self.has_audio = has_audio
    self.frames = {}
    self.basetime = 0
    self.duration = 0
    self.metadata = {
      'width':0, 'height':0, 
      'framerate':framerate, 'duration':0,
      }
    if self.has_video:
      self.metadata['videocodecid'] = 3
      self.frames[0] = []
    if self.has_audio:
      self.metadata['audiocodecid'] = 2
      self.frames[1] = []
    self.write_header()
    return

  def write_object(self, obj):
    if isinstance(obj, bool):
      self.write('\x01'+chr(obj))
    elif isinstance(obj, (int, long, float)):
      self.write('\x00'+pack('>d', obj))
    elif isinstance(obj, (str, unicode)):
      if isinstance(obj, unicode):
        obj = obj.encode('utf-8')
      if 65535 < len(obj):
        self.write('\x0c'+pack('>L', len(obj))+obj)
      else:
        self.write('\x02'+pack('>H', len(obj))+obj)
    elif isinstance(obj, list):
      self.write('\x0a'+pack('>L', len(obj)))
      for x in obj:
        self.write_object(x)
    elif isinstance(obj, dict):
      self.write('\x08'+pack('>L', len(obj)))
      for (k,v) in obj.iteritems():
        assert isinstance(k, str)
        self.write(pack('>H', len(k))+k)
        self.write_object(v)
    return

  def write_header(self):
    if self.debug:
      print >>sys.stderr, ('write_header: flv_version=%r, audio=%r, video=%r' %
                           (self.flv_version, self.has_audio, self.has_video))
    self.write('FLV%c' % self.flv_version)
    self.writebits(5,0)
    self.writebits(1,int(self.has_audio))
    self.writebits(1,0)
    self.writebits(1,int(self.has_video))
    self.finishbits()
    self.writeub32(9) # dataoffset (header size) = 9
    self.writeub32(0) # previous tag size = 0
    self.metadata_pos = self.fp.tell()
    self.write_metadata()
    return

  def write_metadata(self):
    if self.debug:
      print >>sys.stderr, 'write_metadata:', self.metadata
    self.start_tag()
    self.write_object('onMetaData')
    self.write_object(self.metadata)
    self.write('\x00\x00\x09')
    self.end_tag(self.TAG_DATA)
    return

  def end_tag(self, tag, timestamp=None):
    data = self.pop()
    if timestamp is not None:
      self.duration = self.basetime+int(timestamp)
    self.writeui8(tag)
    self.writeub24(len(data))
    self.writeub24(self.duration)
    self.writeui32(0)   # reserved
    self.write(data)
    self.writeub32(len(data)+11)  #size of this tag
    return

  def write_other_data(self, tag, data):
    if self.debug:
      print >>sys.stderr, 'write_other_data: tag=%d, data=%d' % (tag, len(data))
    self.start_tag()
    self.write(data)
    self.end_tag(tag)
    return

  def write_video_frame(self, timestamp, data):
    assert self.has_video
    if self.debug:
      print >>sys.stderr, 'write_video_frame: timestamp=%d, data=%d' % (timestamp, len(data))
    self.frames[0].append((timestamp, self.TAG_VIDEO, data))
    self._update()
    return

  def write_audio_frame(self, timestamp, data):
    assert self.has_audio
    if self.debug:
      print >>sys.stderr, 'write_audio_frame: timestamp=%d, data=%d' % (timestamp, len(data))
    self.frames[1].append((timestamp, self.TAG_AUDIO, data))
    self._update()
    return
  
  def _update(self):
    while 1:
      frames = None
      for k in sorted(self.frames.iterkeys()):
        v = self.frames[k]
        if not v: return
        if not frames:
          frames = v
        else:
          (t0,_,_) = v[0]
          (t1,_,_) = frames[0]
          if t0 < t1:
            frames = v
      (timestamp, tag, data) = frames.pop(0)
      self.start_tag()
      self.write(data)
      self.end_tag(tag, timestamp)
    return

  def set_screen_size(self, width, height):
    if self.debug:
      print >>sys.stderr, 'set_screen_size: %dx%d' % (width, height)
    self.metadata['width'] = width
    self.metadata['height'] = height
    return

  def add_basetime(self, t):
    if self.debug:
      print >>sys.stderr, 'add_basetime: %d+%d' % (self.basetime, t)
    self.basetime += t
    return

  def flush(self):
    if self.debug:
      print >>sys.stderr, 'flush'
    for frames in self.frames.itervalues():
      while frames:
        (timestamp, tag, data) = frames.pop(0)
        self.start_tag()
        self.write(data)
        self.end_tag(tag, timestamp)
    return

  def close(self):
    self.flush()
    DataWriter.close(self)
    # re-write metadata
    self.metadata['duration'] = self.duration*.001
    self.duration = 0
    self.fp.seek(self.metadata_pos)
    self.write_metadata()
    self.fp.flush()
    return
  

# test
if __name__ == "__main__": pass
