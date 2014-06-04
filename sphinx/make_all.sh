#!/bin/bash

rm -rf send
mkdir send

cd siren-help/
rm -rf _build
make html
make latexpdf
cp -r _build/html ../send/help
cp _build/latex/Siren.pdf ../send/help/Siren-UserGuide.pdf

cd ../siren-web/
rm -rf _build
make html
cp -r _build/html ../send/main

cd ../siren-sigmod/
rm -rf _build
make singlehtml
make latexpdf
cp -r _build/singlehtml ../send/sigmod
cp _build/latex/Siren.pdf ../send/sigmod/Siren-SIGMOD.pdf


cd ../send/
sed -i 's:\([^/]\)_static/:\1../_static/:g' */*.html
sed -i 's:\([^/]\)_images/:\1../_images/:g' */*.html
mv sigmod/_static ./
mv sigmod/_images ./
mv main/_static/* ./_static/
mv main/_images/* ./_images/
mv help/_static/* ./_static/
mv help/_images/* ./_images/
rmdir help/_images help/_static main/_images main/_static

cd ..
tar -cvzf sphinx-siren-send.tar.gz send
