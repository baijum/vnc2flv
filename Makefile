##  Makefile (for maintainance purpose)
##

PACKAGE=vnc2flv
PREFIX=/usr/local

SVN=svn
PYTHON=python
RM=rm -f
CP=cp -f
LN=ln -fs

all:

install:
	$(PYTHON) setup.py install --prefix=$(PREFIX)

clean:
	-$(PYTHON) setup.py clean
	-$(RM) $(PACKAGE)/*.pyc 
	-$(RM) -r build dist

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

# Maintainance:
commit: clean
	$(SVN) commit

sdist: clean
	$(PYTHON) setup.py sdist

register: clean
	$(PYTHON) setup.py sdist upload register

VERSION=`$(PYTHON) $(PACKAGE)/__init__.py`
WEBDIR=$$HOME/Site/unixuser.org/python/$(PACKAGE)
DISTFILE=$(PACKAGE)-$(VERSION).tar.gz
publish: sdist
	$(CP) dist/$(DISTFILE) $(WEBDIR)
	$(LN) $(DISTFILE) $(WEBDIR)/$(PACKAGE)-current.tar.gz
	$(CP) docs/*.html $(WEBDIR)/
