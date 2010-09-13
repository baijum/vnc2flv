#!/bin/sh
##
##  recordwin.sh - Quick recording script for UNIX.
##
##  Copyright (c) 2009-2010 by Yusuke Shinyama
##
##  usage:
##     recordwin.sh [-host hostname] [-all] [-display disp] [-name winname] [-id winid] [output.flv]
##
##  Requires: x11vnc, xwininfo, arecord, lame, awk, date
##

TMPDIR=/tmp
FLVREC=${FLVREC:-flvrec.py}
FLVADDMP3=${FLVADDMP3:-flvaddmp3.py}
X11VNC=${X11VNC:-x11vnc}
XWININFO=${XWININFO:-xwininfo}
ARECORD=${ARECORD:-arecord}
LAME=${LAME:-lame}
AWK=${AWK:-awk}
id=`date '+%Y%m%d%H%M%S'`.$$

usage() {
    echo "usage: $0 [-host hostname] [-all] [-display display] [-name windowname] [-geometry geometry] [-id windowid] [-type filetype] [outfile]"
    exit 100
}

# Parse arguments.
host=
outfile=
flvrecopts=
xwopts=
desktop=
verbose=
geometry=
display="$DISPLAY"
while [ $# -gt 0 ]; do
    case "$1" in
	-all|-a) desktop=1;;
        -verbose|-v) verbose=1;;
	-name) shift; xwopts="$xwopts -name $1";;
	-id) shift; xwopts="$xwopts -id $1";;
	-display|-disp|-d) shift; display="$1"; xwopts="$xwopts -display $1";;
        -geometry|-geom|-g) shift; geometry="$1";;
	-host) shift; host="$1";;
	-*) usage;;
        *) outfile="$1";;
    esac
    shift
done

if [ "X$host" != "X" ]; then
  flvrecopts="$host"
elif [ "X$geometry" != "X" ]; then
  flvrecopts="-C $geometry"
elif [ "X$desktop" = "X" ]; then
  echo "Please select the window..."
  info=`$XWININFO $xwopts 2>/dev/null`
  if [ "X$info" = "X" ]; then
    echo "Window $xwopts not found!"
    exit 2
  fi
  geometry=`echo "$info" |
               $AWK '/Absolute upper-left X:/{x=$4}
                     /Absolute upper-left Y:/{y=$4}
                     /Width:/{w=$2} /Height:/{h=$2}
                     END {printf "%dx%d+%d+%d",w,h,x,y}' `
  flvrecopts="-C $geometry"
fi

if [ "X$outfile" = "X" ]; then
  outfile=out.$id.flv
fi

tmpbase=$TMPDIR/vnc2flv.$id
flvfile=${tmpbase}.flv
wavfile=${tmpbase}.wav
mp3file=${tmpbase}.mp3

if [ "X$verbose" != "X" ]; then
  echo "output: $outfile"
  echo "opts: $flvrecopts"
fi

# Start recording.
trap ":" INT
# XXX err if the port 5900 is already occupied.
( if [ "X$host" = "X" ]; then
    $X11VNC -quiet -bg -nopw -display "$display" -viewonly -localhost -once
  fi ) &&
  $FLVREC -S "$ARECORD $wavfile" -o "$flvfile" $flvrecopts &&
  [ -f "$flvfile" -a -f "$wavfile" ] &&
  $LAME "$wavfile" "$mp3file" &&
  $FLVADDMP3 -f "$flvfile" "$mp3file" "$outfile" &&
  rm "$flvfile" "$wavfile" "$mp3file"
