export BASEDIR=$PWD
export INSTALLDIR=$PWD/install
export DISTDIR=$PWD/distrib
 
mkdir -p $INSTALLDIR
mkdir -p $DISTDIR
 
cd $DISTDIR 
wget --no-check-certificate https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
wget --no-check-certificate https://pypi.python.org/packages/source/v/virtualenv/virtualenv-12.0.tar.gz
 
tar xvvf virtualenv-*.tar.gz
tar xvvf Python-*.tgz
 
cd $DISTDIR/Python-*/    
./configure CXXFLAGS="-I$INSTALLDIR/include" --prefix=$INSTALLDIR   --enable-shared --enable-unicode=ucs4
make && make install
 
cd $DISTDIR/virtualenv-*/
LD_LIBRARY_PATH=$INSTALLDIR/lib/ $INSTALLDIR/bin/python setup.py install --prefix=$INSTALLDIR
 
cd $BASEDIR
LD_LIBRARY_PATH=$INSTALLDIR/lib/ $INSTALLDIR/bin/virtualenv --python=$INSTALLDIR/bin/python fabric
 
cat > env.sh << "EOF"
MY_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $MY_PATH/fabric/bin/activate
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MY_PATH/install/lib
EOF
 
. env.sh
pip install fabric
