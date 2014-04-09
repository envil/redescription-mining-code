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
sed -i 's:_static/:../_static/:g' */*.html
mv sigmod/_static ./
rm -rf main/_static
rm -rf help/_static

cd ..
tar -cvzf sphinx-siren-send.tar.gz send
