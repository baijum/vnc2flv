#!/usr/bin/env python
##
##  rfb.py - handling VNC protocol.
##
##  Copyright (c) 2009 by Yusuke Shinyama
##

# For the details of RFB protocol,
# see http://www.realvnc.com/docs/rfbproto.pdf

import sys, time, socket
from struct import pack, unpack
from vnc2flv.d3des import decrypt_passwd, generate_response


def byte2bit(s):
  return ''.join([ chr((ord(s[i>>3]) >> (7 - i&7)) & 1) for i in xrange(len(s)*8) ])
def str2bitmap(data, width, height, rowbytes):
  return ''.join([ byte2bit(data[i*rowbytes:(i+1)*rowbytes])[:width] for i in xrange(height) ])


# Exceptions
class RFBError(Exception): pass
class RFBAuthError(RFBError): pass
class RFBProtocolError(RFBError): pass



##  PWDCache
##
class PWDCache(object):
  
  def __init__(self, name):
    self.name = name
    self.p = None
    return
  
  def getpass(self):
    if not self.p:
      import getpass
      self.p = getpass.getpass('Password for %s: ' % self.name)
    return self.p


##  PWDFile
##
class PWDFile(object):
  
  def __init__(self, fname):
    fp = file(fname)
    self.p = fp.read().strip()
    fp.close()
    return
  
  def getpass(self):
    return self.p


##  RFBProxy
##
class RFBProxy(object):

  def __init__(self, sink, pwdcache=None, preferred_encoding=(5,0), debug=0):
    self.sink = sink
    self.pwdcache = pwdcache
    self.preferred_encoding = preferred_encoding
    self.debug = debug
    self.basetime = None
    self.session_open = False
    return

  def preferred_format(self, bitsperpixel, depth, bigendian, truecolour,
                       red_max, green_max, blue_max,
                       red_shift, green_shift, blue_shift):
    # should return 10-tuple (bitsperpixel, depth, bigendian, truecolour,
    #   red_max, green_max, blue_max, red_shift, green_shift, blue_shift)
    return (32, 8, 1, 1, 255, 255, 255, 24, 16, 8)
  
  def send(self, s):
    "Send data s to the server."
    raise NotImplementedError

  def time(self):
    assert self.basetime != None
    return int(time.time()*1000) - self.basetime
  
  def request_update(self):
    if not self.session_open: return
    if self.debug:
      print >>sys.stderr, 'FrameBufferUpdateRequest'
    self.send('\x03\x01' + pack('>HHHH', *self.clipping))
    return

  def open(self):
    self.basetime = int(time.time()*1000)
    self._curbuf = ''
    (self._length, self._state) = self.init()
    return

  def feed(self, data):
    self._curbuf += data
    while self._length <= len(self._curbuf):
      x = self._curbuf[:self._length]
      self._curbuf = self._curbuf[self._length:]
      if self.debug:
        print >>sys.stderr, 'feed: state=%r, data=%r' % (self._state, x[:10])
      (self._length, self._state) = self._state(x)
    return

  def close(self):
    self.session_open = False
    self.sink.flush(self.time())
    self.sink.close()
    return
  
  def init(self):
    return (12, self.init_1)
  def init_1(self, server_version):
    # send: client protocol version
    self.protocol_version = 3
    if server_version.startswith('RFB 003.007'):
      self.protocol_version = 7
    elif server_version.startswith('RFB 003.008'):
      self.protocol_version = 8
    self.send('RFB 003.%03d\x0a' % self.protocol_version)
    if self.debug:
      print >>sys.stderr, 'protocol_version: 3.%d' % self.protocol_version
    if self.protocol_version == 3:
      return self.auth3()
    else:
      return self.auth7()

  def autherr(self):
    return (4, self.autherr_1)
  def autherr_1(self, data):
    # receive reason length
    (reason_length,) = unpack('>L', data)
    return (reason_length, self.autherr_2)
  def autherr_2(self, reason):
    # receive reason string
    raise RFBAuthError('Auth Error: %s' % reason)

  def auth3(self):
    # protocol 3.3 (or 3.6)
    # recv: server security
    return (4, self.auth3_1)
  def auth3_1(self, data):
    (server_security,) = unpack('>L', data)
    if self.debug:
      print >>sys.stderr, 'server_security: %r' % server_security
    # server_security might be 0, 1 or 2.
    if server_security == 0:
      return self.autherr()
    elif server_security == 1:
      return self.start()
    else:
      return self.crauth()
    
  def auth7(self):
    # protocol 3.7 or 3.8
    # recv: multiple server securities
    return (1, self.auth7_1)
  def auth7_1(self, data):
    (nsecurities,) = unpack('>B', data)
    return (nsecurities, self.auth7_2)
  def auth7_2(self, server_securities):
    if self.debug:
      print >>sys.stderr, 'server_securities: %r' % server_securities
    # must include None or VNCAuth
    if '\x01' in server_securities:
      # None
      self.send('\x01')
      if self.protocol_version == 8:
        # Protocol 3.8: must recv security result
        return (4, self.auth8_3)
      else:
        return self.authend(0)
    elif '\x02' in server_securities:
      # VNCAuth
      self.send('\x02')
      return self.crauth()
    raise RFBAuthError('Unknown security: %r' % server_securities)
  def auth8_3(self, data):
    (server_result,) = unpack('>L', data)
    return self.authend(server_result)

  def crauth(self):
    # vnc challange & response auth
    return (16, self.crauth_1)
  def crauth_1(self, challange):
    if self.debug:
      print >>sys.stderr, 'challange: %r' % challange
    if not self.pwdcache:
      raise RFBError('Auth cancelled')
    p = self.pwdcache.getpass()
    response = generate_response(p, challange)
    if self.debug:
      print >>sys.stderr, 'response: %r' % response
    self.send(response)
    return (4, self.crauth_2)
  def crauth_2(self, data):
    (server_result,) = unpack('>L', data)
    return self.authend(server_result)

  def authend(self, server_result):
    # result returned.
    if self.debug:
      print >>sys.stderr, 'server_result: %r' % server_result
    if server_result != 0:
      # auth failed.
      if self.protocol_version != 3:
        return self.autherr()
      else:
        reason = server_result
      raise RFBAuthError('Auth Error: %s' % reason)
    # negotiation ok.
    # send: always shared.
    self.send('\x01')
    return self.start()

  def start(self):
    # get server info.
    return (24, self.start_1)
  def start_1(self, server_init):
    (self.width, self.height, self.pixelformat, namelen) = unpack('>HH16sL', server_init)
    return (namelen, self.start_2)
  def start_2(self, name):
    self.name = name
    (bitsperpixel, depth, bigendian, truecolour,
     red_max, green_max, blue_max,
     red_shift, green_shift, blue_shift) = unpack('>BBBBHHHBBBxxx', self.pixelformat)
    if self.debug:
      print >>sys.stderr, 'Server Encoding:'
      print >>sys.stderr, ' width=%d, height=%d, name=%r' % (self.width, self.height, self.name)
      print >>sys.stderr, ' pixelformat=', (bitsperpixel, depth, bigendian, truecolour)
      print >>sys.stderr, ' rgbmax=', (red_max, green_max, blue_max)
      print >>sys.stderr, ' rgbshift=', (red_shift, green_shift, blue_shift)
    # setformat
    self.send('\x00\x00\x00\x00')
    # 32bit, 8bit-depth, big-endian(RGBX), truecolour, 255max
    (bitsperpixel, depth, bigendian, truecolour,
     red_max, green_max, blue_max,
     red_shift, green_shift, blue_shift) = self.preferred_format(bitsperpixel, depth, bigendian, truecolour,
                                                                 red_max, green_max, blue_max,
                                                                 red_shift, green_shift, blue_shift)
    self.bytesperpixel = bitsperpixel/8
    pixelformat = pack('>BBBBHHHBBBxxx', bitsperpixel, depth, bigendian, truecolour,
                       red_max, green_max, blue_max,
                       red_shift, green_shift, blue_shift)
    self.send(pixelformat)
    self.clipping = self.sink.init_screen(self.width, self.height, self.name)
    self.send('\x02\x00' + pack('>H', len(self.preferred_encoding)))
    for e in self.preferred_encoding:
      self.send(pack('>l', e))
    self.session_open = True
    return self.loop()

  def loop(self):
    self.request_update()
    return (1, self.loop_1)
  
  def loop_1(self, c):
    if c == '\x00':
      # framebuffer update
      return self.framebegin()
    elif c == '\x01':
      # change color map
      return self.cmap()
    elif c == '\x02':
      # bell
      if self.debug:
        print >>sys.stderr, 'Bell'
      return self.loop()
    elif c == '\x03':
      # cut-and-paste
      return self.cutnpaste()
    else:
      # others
      raise RFBProtocolError('Unsupported msg: %d' % ord(c))

  def cutnpaste(self):
    return (7, self.cutnpaste_1)
  def cutnpaste_1(self, data):
    (length,) = unpack('>3xL', data)
    return (length, self.cutnpaste_2)
  def cutnpaste_2(self, data):
    if self.debug:
      print >>sys.stderr, 'ServerCutText: %r' % data
    return self.loop()

  def cmap(self):
    return (11, self.cmap_1)
  def cmap_1(self, data):
    (first, ncolours) = unpack('>xHH', data)
    if self.debug:
      print >>sys.stderr, 'SetColourMapEntries: first=%d, ncolours=%d' % (first, ncolours)
    return (ncolours*6, self.cmap_2)
  def cmap_2(self, data):
    return self.loop()

  def framebegin(self):
    return (3, self.frame_1)
  def frameend(self):
    self.sink.flush(self.time())
    return self.loop()

  def frame_1(self, data):
    (nrects,) = unpack('>xH', data)
    if self.debug:
      print >>sys.stderr, 'FrameBufferUpdate: nrects=%d' % nrects
    self.nrects = nrects
    return self.framerect()
  def framerect(self):
    if self.nrects:
      self.nrects -= 1
      return (12, self.framerect_1)
    else:
      return self.frameend()
  def framerect_1(self, data):
    (x, y, width, height, enc) = unpack('>HHHHl', data)
    self.rectpos = (x, y)
    self.rectsize = (width, height)
    if self.debug:
      print >>sys.stderr, ' %d x %d at (%d,%d), enc=%d' % (width, height, x, y, enc)
    if enc == 0:
      # RawEncoding
      return self.encraw(width, height)
    elif enc == 1:
      # CopyRectEncoding (NOT SUPPORTED)
      raise RFBProtocolError('Unsupported encoding: 0x%02x' % enc)
    elif enc == 2:
      # RREEncoding
      return self.encrre()
    elif enc == 4:
      # CoRREEncoding (NOT SUPPORTED)
      raise RFBProtocolError('Unsupported encoding: 0x%02x' % enc)
    elif enc == 5:
      # HextileEncoding (NOT SUPPORTED)
      raise RFBProtocolError('Unsupported encoding: 0x%02x' % enc)
    elif enc == 16:
      # ZRLEEncoding (NOT SUPPORTED)
      raise RFBProtocolError('Unsupported encoding: 0x%02x' % enc)
    elif enc == -239:
      # RichCursor
      return self.richcursor(width, height)
    elif enc == -240:
      # XCursor
      return self.xcursor(width, height)
    elif enc == -232:
      # CursorPos -> only change the cursor position
      return self.cursorpos(x, y)
    else:
      raise RFBProtocolError('Unsupported encoding: 0x%02x' % enc)

  def encraw(self, width, height):
    return (width*height*self.bytesperpixel, self.encraw_1)
  def encraw_1(self, data):
    if self.debug:
      print >>sys.stderr, ' RawEncoding: received=%d' % (len(data))
    self.sink.update_screen_rgbabits(self.rectpos, self.rectsize, data)
    return self.framerect()

  def enccopy(self):
    return (4, self.enccopy_1)
  def enccopy_1(self):
    return self.framerect()

  def encrre(self):
    return (4, self.encrre_1)
  def encrre_1(self, data):
    (self.nsubrects,) = unpack('>L', data)
    return (self.bytesperpixel, self.encrre_2)
  def encrre_2(self, bgcolor):
    if self.debug:
      print >>sys.stderr, ' RREEncoding: subrects=%d, bgcolor=%r' % (self.nsubrects, bgcolor)
    self.sink.update_screen_solidrect(self.rectpos, self.rectsize, bgcolor)
    return self.encrre_subrect()
  def encrre_subrect(self):
    if self.nsubrect:
      self.nsubrect -= 1
      return (self.bytesperpixel, self.encrre_subrect_1)
    else:
      return self.framerect()
  def encrre_subrect_1(self, fgcolor):
      fgcolor = self.recv(self.bytesperpixel)
      (x,y,w,h) = unpack('>HHHH', self.recv(8))
      if 2 <= self.debug:
        print >>sys.stderr, ' RREEncoding: ', (x,y,w,h,fgcolor)
      (x0,y0) = self.rectpos
      self.sink.update_screen_solidrect((x0+x, y0+y), (w, h), fgcolor)
      return self.encrre_subrect()
    
  def richcursor(self, width, height):
    if width == 0 or height == 0:
      return self.framerect()
    rowbytes = (width + 7) / 8
    return (width*height*self.bytesperpixel + rowbytes*height, self.richcursor_1)
  def richcursor_1(self, data):
    (x,y) = self.rectpos
    (width,height) = self.rectsize
    rowbytes = (width + 7) / 8
    # Cursor image RGB
    n = width*height*self.bytesperpixel
    image = data[:n]
    # Cursor mask -> 1 bit/pixel (1 -> image; 0 -> transparent)
    mask = data[n:]
    # Set the alpha channel with maskData where bit=1 -> alpha = 255, bit=0 -> alpha=255
    if self.debug:
      print >>sys.stderr, 'RichCursor: %dx%d at %d,%d' % (width,height,x,y)
    image = self.sink.convert_pixels(image)
    mask = str2bitmap(mask, w, h, rowbytes)
    def conv1(i):
      if mask[i/4] == '\x01':
        return '\xff'+image[i]+image[i+1]+image[i+2]
      else:
        return '\x00\x00\x00\x00'
    bits = ''.join([ conv1(i) for i in xrange(0, len(image), 4) ])
    self.sink.update_cursor_image(width, height, bits)
    self.sink.update_cursor_pos(x, y)
    return

  def xcursor(self, width, height):
    if width == 0 or height == 0:
      return self.framerect()
    rowbytes = (width + 7) / 8
    return (3+3+2*rowbytes*height, self.xcursor_1)
  def xcursor_1(self, data):
    (x,y) = self.rectpos
    (width,height) = self.rectsize
    rowbytes = (width + 7) / 8
    # Foreground RGB
    fgcolor = data[:3]
    # Background RGB
    bgcolor = data[3:6]
    n = rowbytes*height
    # Cursor Data -> 1 bit/pixel
    shape = data[6:6+n]
    # Cursor Mask -> 1 bit/pixel
    mask = data[6+n:]
    # Create the image from cursordata and maskdata.
    if self.debug:
      print >>sys.stderr, 'XCursor: %dx%d at %d,%d' % (width,height,x,y)
    shape = str2bitmap(shape, width, height, rowbytes)
    mask = str2bitmap(mask, width, height, rowbytes)
    def conv1(i):
      if mask[i] == '\x01':
        if shape[i] == '\x01':
          return '\xff'+fgcolor
        else:
          return '\xff'+bgcolor
      else:
        return '\x00\x00\x00\x00'
    bits = ''.join([ conv1(i) for i in xrange(len(shape)) ])
    self.sink.update_cursor_image(width, height, bits)
    self.sink.update_cursor_pos(x, y)
    return

  def cursorpos(self, x, y):
    if self.debug:
      print >>sys.stderr, 'CursorPos: %d,%d' % (x,y)
    self.sink.update_cursor_pos(x, y)
    return self.framerect()


##  RFBNetworkClient
##
class RFBNetworkClient(RFBProxy):
  
  def __init__(self, host, port, sink, timeout=50, bufsiz=65536,
               pwdcache=None, preferred_encoding=(0,5), debug=0):
    RFBProxy.__init__(self, sink, 
                      pwdcache=pwdcache, preferred_encoding=preferred_encoding, debug=debug)
    self.host = host
    self.port = port
    self.timeout = timeout
    self.bufsiz = bufsiz
    return

  def open(self):
    RFBProxy.open(self)
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((self.host, self.port))
    self.sock.settimeout(self.timeout*.001)
    if self.debug:
      print >>sys.stderr, 'Connected: %s:%d' % (self.host, self.port)
    return

  def idle(self):
    try:
      data = self.sock.recv(self.bufsiz)
      if not data: raise RFBProtocolError('unexpected EOF')
      self.feed(data)
    except socket.timeout:
      if self.session_open:
        self.sink.flush(self.time())
    return

  def send(self, s):
    return self.sock.send(s)
    
  def close(self):
    RFBProxy.close(self)
    self.sock.close()
    return


# test
if __name__ == '__main__':
  from vnc2flv.video import VideoSink
  sink = VideoSink()
  client = RFBNetworkClient('127.0.0.1', 5900, sink, debug=1)
  client.open()
  while 1:
    client.idle()
  client.close()
