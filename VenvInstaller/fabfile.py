import StringIO
from fabric.api import *

BASEDIR    = "VirtualEnv"
DISTDIR    = BASEDIR + "/distribs"
INSTALLDIR = BASEDIR + "/install"

env.hosts = [
#    "root@kanishev-ams-vm0",
    "root@kanishev-ams-vm1",
    "root@kanishev-ams-vm2",
    "root@kanishev-ams-vm3",
    "root@kanishev-ams-vm4",
]

envsh = StringIO.StringIO("""
MY_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $MY_PATH/install/bin/thisroot.sh
source $MY_PATH/ipython/bin/activate
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MY_PATH/install/lib
""")

def yum():
    packages = [
        "openssl-devel", "xorg-x11-server-devel", "gcc-gfortran",
        "gcc-c++", "gcc", "binutils", "libX11-devel", 
        "libXpm-devel", "libXft-devel", "libXext-devel",
	"cmake"]
        
    run("yum -y install " + " ".join(packages))


def get_sources():
    packages = [
        "https://sqlite.org/2014/sqlite-autoconf-3080403.tar.gz",
        "http://download.zeromq.org/zeromq-4.0.3.tar.gz",
        "https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz",
        "https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.9.tar.gz",
        "ftp://root.cern.ch/root/root_v5.34.18.source.tar.gz"
    ]
    run("mkdir -p " + DISTDIR)
    with cd(DISTDIR):
        for p in packages:
            run("wget " + p)
        for p in packages:
            run("tar xvvf " + p.split("/")[-1])


def compile():
    run("mkdir -p " + INSTALLDIR)
    with cd(DISTDIR + "/sqlite-autoconf-*"):
        run("./configure --prefix=$HOME/" + INSTALLDIR)
        run("make && make install")
 
    with cd(DISTDIR + "/zeromq-*"):
        run("./configure --prefix=$HOME/" + INSTALLDIR)
        run("make && make install")

    with cd(DISTDIR + "/Python-2.7.6"):
        run('./configure CXXFLAGS="-I$HOME/{0}/include" --prefix=$HOME/{0}   --enable-shared --enable-unicode=ucs4'.format(INSTALLDIR))
        run("make && make install")

    with cd("$HOME/{0}/lib".format(INSTALLDIR)):
        with settings(warn_only=True):
	     run("ln -s libpython2.7.so libpython.so")

    with cd("$HOME/{0}/root".format(DISTDIR)):
        version = "4.1.1"
        instdir = "$HOME/{0}/opt".format(INSTALLDIR)

        run("mkdir -p " + instdir)
        run("./build/unix/installXrootd.sh -v {0} $HOME/{1}/opt".format(version,INSTALLDIR))
        
        confcommand = [ 
            "./configure",
            "--with-python-incdir=$HOME/{0}/include/python2.7/".format(INSTALLDIR),
            "--with-python-libdir=$HOME/{0}/lib".format(INSTALLDIR),
            "--prefix=$HOME/{0}".format(INSTALLDIR),
            "--etcdir=$HOME/{0}/etc".format(INSTALLDIR),
            "--with-xrootd-incdir=$HOME/{0}/opt/xrootd-{1}/include/xrootd".format(INSTALLDIR, version),
            "--with-xrootd-libdir=$HOME/{0}/opt/xrootd-{1}/lib".format(INSTALLDIR, version) ]
        run(" ".join(confcommand))

        run("make && make install")

def install_numpy():
    with cd(DISTDIR):
        run("git clone git://github.com/xianyi/OpenBLAS")
        with(cd("OpenBLAS")):
            run("make FC=gfortran")
            run("make PREFIX=$HOME/{0} install".format(INSTALLDIR))
 
    with cd(DISTDIR):
        run("mkdir -p numpy")
        run("source env.sh && pip install -d numpy numpy")
        with cd("numpy"):
            run("tar xvvf numpy-*.tar.gz")
            with cd("numpy-*"):
                put(StringIO.StringIO("""
                    [default]
                    library_dirs= $INSTALLDIR/lib/
                    [openblas]
                    libraries = openblas
                    library_dirs = $INSTALLDIR/lib
                    include_dirs = $INSTALLDIR/include"""), "site.cfg")
                run("$HOME/{0}/source env.sh && python setup.py install".format(DISTDIR))
	run("source  env.sh && pip install scipy")

def prepare_venv():
    with cd(BASEDIR):
        run("cp $HOME/{0}/virtualenv-1.9/virtualenv.py .".format(DISTDIR))
        run("LD_LIBRARY_PATH=$HOME/{0}/lib/ $HOME/{0}/bin/python virtualenv.py --python=$HOME/{0}/bin/python ipython".format(INSTALLDIR))

        put(envsh, "env.sh")

        run('source env.sh && pip install pyzmq --install-option="--zmq=$HOME/{0}"'.format(INSTALLDIR))
        run('source env.sh && CPPFLAGS="-I$HOME/{0}/include" pip install pysqlite'.format(INSTALLDIR))
         
        run('source env.sh && pip install ipython[all]')
