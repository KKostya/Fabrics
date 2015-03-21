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

def yum():
    packages = ["rabbitmq-server"] 
    run("yum -y install " + " ".join(packages))
