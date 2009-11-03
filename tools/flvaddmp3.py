#!/usr/bin/env python
##
##  flvaddmp3.py - put an mp3 audio to an existing FLV movie.
##
##  Copyright (c) 2009 by Yusuke Shinyama
##

import sys, os, re
from vnc2flv.flv import FLVParser, FLVWriter
from vnc2flv.audio import AudioBuffer
from vnc2flv.video import MultipleRange


##  mp3add
##
def mp3add(srcfile, mp3files, outfile, force=False, debug=0):
  if not force:
    try:
      os.stat(outfile)
      raise IOError('file already exists: %r' % outfile)
    except OSError:
      pass
  fout = file(outfile, 'wb')
  writer = FLVWriter(fout, debug=debug, has_video=True, has_audio=True)
  fin = file(srcfile, 'rb')
  parser = FLVParser(fin, debug=debug)
  for (i, (tag, _, timestamp, _)) in enumerate(parser):
    if tag == 8:
      pass
    elif tag == 9:
      writer.write_video_frame(timestamp, parser.get_data(i))
    elif tag == 18:
      (k,v) = parser.parse_metadata(parser.get_data(i))
      if k == 'onMetaData':
        writer.set_screen_size(v.get('width',0), v.get('height',0))
      else:
        writer.write_other_data(tag, parser.get_data(i))
  parser.close()
  fin.close()
  for fname in mp3files:
    m = re.match(r'([^:]+):(.+)$', fname)
    ranges = None
    if m:
      fname = m.group(1)
      ranges = MultipleRange(m.group(2))
    audio = AudioBuffer()
    fp = file(fname, 'rb')
    audio.load(fp)
    fp.close()
    if ranges:
      for (_,s,e) in ranges:
        audio.put(writer, s, e, s)
    else:
      audio.put(writer)
  writer.close()
  fout.close()
  return


# main
def main(argv):
  import getopt, vnc2flv
  def usage():
    print argv[0], vnc2flv.__version__
    print ('usage: %s [-d] [-f] input.flv [mp3:range ...] output.flv' % argv[0])
    return 100
  try:
    (opts, args) = getopt.getopt(argv[1:], 'df')
  except getopt.GetoptError:
    return usage()
  debug = 0
  force = False
  for (k, v) in opts:
    if k == '-d': debug += 1
    elif k == '-f': force = True
  if len(args) < 3: return usage()
  srcfile = args.pop(0)
  outfile = args.pop(-1)
  mp3add(srcfile, args, outfile, force=force, debug=debug)
  return

if __name__ == "__main__": sys.exit(main(sys.argv))
