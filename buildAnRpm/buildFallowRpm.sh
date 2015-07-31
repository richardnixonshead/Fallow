#!/bin/bash

mkdir tmp/
cd tmp/

scp  ../../scripts/* .

V=`grep "define version" ../SPECS/fallow.spec  | sed -e "s/.*\s//"`
D=fallow-$V
mkdir $D

mv fallow.py $D
mv runFallow.sh $D
mv fallow $D
rm *[Ff]allow*

tar -cvf $D.tar $D
rm -rf $D
gzip $D.tar
mv $D.tar.gz ../SOURCES
rm -rf $D.tar.gz $D

cd ..
rm -rf tmp/
rpmbuild  -ba  SPECS/fallow.spec

