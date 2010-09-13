##  Makefile (for maintainance purpose)
##

PACKAGE=vnc2flv

PYTHON=python
GIT=git
RM=rm -f
CP=cp -f

all:

install:
	$(PYTHON) setup.py install --home=$(HOME)

clean:
	-$(PYTHON) setup.py clean
	-$(RM) -r build dist MANIFEST
	-cd $(PACKAGE) && $(MAKE) clean

distclean: clean

pack: distclean MANIFEST
	$(PYTHON) setup.py sdist
register: distclean MANIFEST
	$(PYTHON) setup.py sdist upload register
MANIFEST:
	$(GIT) ls-tree --name-only -r HEAD > MANIFEST

WEBDIR=$$HOME/Site/unixuser.org/python/$(PACKAGE)
publish:
	$(CP) docs/*.html $(WEBDIR)/

# for testing

debug:
	x11vnc -quiet -localhost -viewonly -nopw -bg
	PYTHONPATH=. $(PYTHON) -m vnc2flv.video

runvnc:
	x11vnc -quiet -localhost -viewonly -nopw -bg -many
recmp3:
	arecord -f cd -c 1 -D input - | lame -f - sample.mp3

testflvscreen:
	$(PYTHON) setup.py build
	PYTHONPATH=build/lib.linux-i686-2.5 $(PYTHON) flvscreen/test.py
