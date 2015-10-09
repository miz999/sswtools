#!/usr/bin/bash -e

cd "${HOME}/src/sswtools/"

for f in `ls -1 *.py`
do
    lastm=`stat $f -c %y | sed -En "s/^([0-9]+)-([0-9]+)-([0-9]+).*/\1\2\3/p"`
    sed -i "s/^__version__.*/__version__ = $lastm/" $f
done
         
