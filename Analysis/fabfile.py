import StringIO
from fabric.api import *

env.forward_agent = True

env.hosts = [
    "root@kanishev-ams-vm0",
    "root@kanishev-ams-vm1",
    "root@kanishev-ams-vm2",
    "root@kanishev-ams-vm3",
    "root@kanishev-ams-vm4",
]

def update():
    with cd("AMSDeutons"):
        run("git pull")
        run("source amsvar.sh.lxplus && make")

