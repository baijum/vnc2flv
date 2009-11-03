#!/usr/bin/env python
##
##  flvcat.py - FLV movie concatination tool.
##
##  Copyright (c) 2009 by Yusuke Shinyama
##

import sys, os, re
from vnc2flv.flv import FLVWriter, FLVParser
from vnc2flv.audio import AudioBuffer
from vnc2flv.video import str2clip, str2size, MultipleRange, FLVVideoSink, FLVMovieProcessor


##  flvcat
##
def flvcat(outfile, srcfiles,
           framerate=12, keyframe=120,
           blocksize=32, clipping=None,
           panwindow=None, panspeed=0,
           force=False, debug=0):
    if not force:
        try:
            os.stat(outfile)
            raise IOError('file already exists: %r' % outfile)
        except OSError:
            pass
    fout = file(outfile, 'wb')
    writer = FLVWriter(fout, has_video=True, has_audio=True, framerate=framerate, debug=debug)
    processor = FLVMovieProcessor(writer=writer, debug=debug)
    for fname in srcfiles:
        ranges = None
        m = re.match(r'([^:]+):(.+)$', fname)
        if m:
            fname = m.group(1)
            ranges = MultipleRange(m.group(2))
        fin = file(fname, 'rb')
        parser = FLVParser(fin)
        audiobuf = AudioBuffer()
        videosink = FLVVideoSink(writer, framerate=framerate, keyframe=keyframe,
                                 blocksize=blocksize, clipping=clipping,
                                 panwindow=panwindow, panspeed=panspeed,
                                 debug=debug)
        processor.process_flv(parser, audiobuf, videosink, ranges=ranges)
        parser.close()
        fin.close()
    writer.close()
    fout.close()
    return


# main
def main(argv):
    import getopt, vnc2flv
    def usage():
        print argv[0], vnc2flv.__version__
        print ('usage: %s [-d] [-f] [-r framerate] [-K keyframe]'
               ' [-B blocksize] [-C clipping] [-W panwindow] [-S panspeed]'
               ' src1.flv src2.flv ... dest.flv' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'dfr:K:B:C:W:S:')
    except getopt.GetoptError:
        return usage()
    debug = 0
    force = False
    framerate = 12
    keyframe = 120
    blocksize = 32
    clipping = None
    panwindow = None
    panspeed = 15
    (host, port) = ('localhost', 5900)
    for (k, v) in opts:
        if k == '-d': debug += 1
        elif k == '-f': force = True
        elif k == '-r': framerate = int(v)
        elif k == '-K': keyframe = int(v)
        elif k == '-B': blocksize = int(v)
        elif k == '-C': clipping = str2clip(v)
        elif k == '-W': panwindow = str2size(v)
        elif k == '-S': panspeed = int(v)
    if len(args) < 2: return usage()
    outfile = args.pop(-1)
    srcfiles = args
    flvcat(outfile, srcfiles,
           framerate=framerate, keyframe=keyframe,
           blocksize=blocksize, clipping=clipping,
           panwindow=panwindow, panspeed=panspeed,
           force=force, debug=debug)
    return

if __name__ == "__main__": sys.exit(main(sys.argv))
