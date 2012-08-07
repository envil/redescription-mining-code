
PYTHON=/usr/bin/python
### `which python`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/siren
PROJECT=python-siren
VERSION=1.0

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

	mkdir -p $(DESTDIR)/usr/share/icons/hicolor/32x32/apps/
	cp siren/icons/siren_icon32x32.png $(DESTDIR)/usr/share/icons/hicolor/32x32/apps/siren.png

	mkdir -p $(DESTDIR)/usr/share/applications/
	cp siren_desktop $(DESTDIR)/usr/share/applications/siren.desktop

	mkdir -p $(DESTDIR)/usr/share/mime/x-content/
	cp x-siren.xml $(DESTDIR)/usr/share/mime/x-content/	

	mkdir -p $(DESTDIR)/usr/share/mimelnk/x-content/
	cp x-siren_desktop $(DESTDIR)/usr/share/mimelnk/x-content/x-siren.desktop	

	mkdir -p $(DESTDIR)/usr/bin
	cp exec_siren.py $(DESTDIR)/usr/bin
	chmod a+x $(DESTDIR)/usr/bin/exec_siren.py

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

builddeb:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=../
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)-$$1\.orig\.tar\.gz/' ../*
	# build the package
	dpkg-buildpackage -i"(.svn|dist|outputs|.*icons.*|commons\/web_.*|.*.rtf)" -rfakeroot

clean:
	$(PYTHON) setup.py clean
	#$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete
