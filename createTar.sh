

ver="0.2"
file=cbs-public-$ver

cd ..

tar -cvf $file.tar cbs-public
gzip $file.tar
mv $file.tar.gz /tmp/

echo "  Tar file is in /tmp/$file.tar.gz"

