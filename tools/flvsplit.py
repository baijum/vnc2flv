#!/usr/bin/env python
##
##  flvsplit.py - FLV movie split tool.
##
##  Copyright (c) 2010 by Yusuke Shinyama
##

import sys, os.path, re
from vnc2flv.flv import FLVWriter, FLVParser
from vnc2flv.audio import AudioSink
from vnc2flv.video import MultipleRange, FLVVideoSink, FLVMovieProcessor


##  flvsplit
##
def flvsplit(outbase, srcfile, 
             framerate=12, keyframe=120, blocksize=32,
             duration=sys.maxint, overlap=0, format='%s-%03d.flv',
             force=False, debug=0):
    fin = file(srcfile, 'rb')
    parser = FLVParser(fin)
    totaldur = parser.get_duration()
    (_,_,totaldur,_,_) = parser[-1]
    print >>sys.stderr, 'total duration: %d' % totaldur
    t0 = 0
    i = 0
    while 1:
        outfile = format % (outbase, i)
        if not force and os.path.exists(outfile):
            raise IOError('file already exists: %r' % outfile)
        fout = file(outfile, 'wb')
        writer = FLVWriter(fout, has_video=True, has_audio=True,
                           framerate=framerate, debug=debug)
        processor = FLVMovieProcessor(writer=writer, debug=debug)
        audiosink = AudioSink()
        videosink = FLVVideoSink(writer, framerate=framerate, keyframe=keyframe,
                                 blocksize=blocksize, debug=debug)
        t1 = min(t0+duration, totaldur)
        print >>sys.stderr, 'writing %r (%d-%d)...' % (outfile, t0, t1)
        ranges = MultipleRange([(t0, t1)])
        processor.process_flv(parser, audiosink, videosink, ranges=ranges)
        writer.close()
        fout.close()
        if totaldur <= t1: break
        t0 = max(0, t1-overlap)
        i += 1
    parser.close()
    fin.close()
    return


# main
def main(argv):
    import getopt, vnc2flv
    def usage():
        print argv[0], vnc2flv.__version__
        print ('usage: %s [-d] [-f] [-r framerate] [-K keyframe]'
               ' [-B blocksize] [-D duration] [-P overlap] [-F format]'
               ' src.flv destbase' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'dfr:K:B:D:P:F:')
    except getopt.GetoptError:
        return usage()
    debug = 0
    force = False
    framerate = 12
    keyframe = 120
    blocksize = 32
    format = '%s-%03d.flv'
    duration = 600*1000
    overlap = 5*1000
    for (k, v) in opts:
        if k == '-d': debug += 1
        elif k == '-f': force = True
        elif k == '-r': framerate = int(v)
        elif k == '-K': keyframe = int(v)
        elif k == '-B': blocksize = int(v)
        elif k == '-D': duration = int(v)*1000
        elif k == '-P': overlap = int(v)*1000
        elif k == '-F': format = v
    if len(args) < 2: return usage()
    srcfile = args.pop(0)
    outbase = args.pop(0)
    try:
        flvsplit(outbase, srcfile,
                 framerate=framerate, keyframe=keyframe, blocksize=blocksize,
                 duration=duration, overlap=overlap, format=format,
                 force=force, debug=debug)
    except IOError, e:
        print >>sys.stderr, e
    return

if __name__ == "__main__": sys.exit(main(sys.argv))
