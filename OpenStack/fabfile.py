import StringIO
from fabric.api import *

env.hosts = [
#    "root@kanishev-ams-vm0",
#    "root@kanishev-ams-vm1",
    "root@kanishev-ams-vm2",
#    "root@kanishev-ams-vm3",
#    "root@kanishev-ams-vm4"
]

krbconf = StringIO.StringIO("""
[libdefaults]
    default_realm = CERN.CH
    ticket_lifetime = 24h
    renew_lifetime = 7d
    forwardable = true
 
[realms]
    CERN.CH = {
        default_domain = cern.ch
        kdc = cerndc.cern.ch
    }
 
[domain_realm]
    cern.ch = CERN.CH
    .cern.ch = CERN.CH """)

def setup_afs(user="kostams"):
    packages = [
        "krb5-workstation", "krb5-libs", "krb5-auth-dialog",
        "openafs-client",  "openafs-server", "openafs-krb5",
        "kernel-module-openafs", "compat-readline5.x86_64",
        "openssl098e.x86_64",  "fuse-libs.x86_64"]

    run("yum -y install " + " ".join(packages))

    put(krbconf, "/etc/krb5.conf")

    run("kinit {0}@CERN.CH".format(user))
    with settings(warn_only=True):
       run("service afs start")
    run("aklog")


cvmfs = StringIO.StringIO("""
    CVMFS_HTTP_PROXY=\"http://ca-proxy.cern.ch:3128;http://ca-proxy1.cern.ch:3128|http://ca-proxy2.cern.ch:3128|http://ca-proxy3.cern.ch:3128|http://ca-proxy4.cern.ch:3128|http://ca-proxy5.cern.ch:3128\"
    CVMFS_REPOSITORIES=ams
""")

def setup_cvmfs():
    with  cd("/etc/yum.repos.d/"):
        run("wget http://cvmrepo.web.cern.ch/cvmrepo/yum/cernvm.repo")

    with cd("/etc/pki/rpm-gpg/"):
        run("wget http://cvmrepo.web.cern.ch/cvmrepo/yum/RPM-GPG-KEY-CernVM")

    run("yum -y install cvmfs.x86_64")

    put(cvmfs, "/etc/cvmfs/default.local")
    put(StringIO.StringIO(
        'CVMFS_SERVER_URL="http://cvmfs-stratum-one.cern.ch/opt/@org@"'
        ), "/etc/cvmfs/config.d/ams.cern.ch.local"
    )
    run("service autofs restart")    
    run("cvmfs_config setup")
    with settings(warn_only=True):
        run("cvmfs_config probe")


def mount_data():
    run("if ! grep -qs '/dev/vda3' /proc/mounts; then mount /dev/vda3 /data; fi")


def mount_all(user="kostams"):
    afshome = '/afs/cern.ch/user/{0}/{1}'.format(user[0],user)
    run("kinit {0}@CERN.CH".format(user))
    run("aklog")
    mount_data()
    test_eos(user=user) 

def test_eos(user="kostams"):
    afshome = '/afs/cern.ch/user/{0}/{1}'.format(user[0],user)
    with settings(warn_only=True):
       ls = run(" ls {0}/eos/ams/user/k/kostams".format(afshome))
       if (not ls) or ("No such file or directory" in ls):
           print "Cannot access eos, remounting"
           run("GROUP=va /afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select -b fuse umount {0}/eos".format(afshome))
           run("GROUP=va /afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select -b fuse mount {0}/eos".format(afshome))


def create_partition(): 
    fdisk = run("fdisk -l -u /dev/vda")
    N, last, ptype = None, None, None
    for l in fdisk.split('\n'):
        if not l.startswith("/dev/vda"):
            continue
        pinfo = l.split()
        if pinfo[1] == '*': del pinfo[1]
        N, last, ptype = int(pinfo[0][-1]), int(pinfo[2]), pinfo[4]
        print "{0}: Found partition '{1}'".format(N,pinfo[0])
        print " -- last block {}".format(last)
        print " -- type {}".format(ptype)

    if N == 2:
        print "There are only two partitons -- creating the third one"
        with settings(warn_only=True):
            run("echo -e 'u\nn\np\n{0}\n{1}\n\nt\n{0}\n{2}\nw\n' | fdisk /dev/vda".format(N+1,last+1,ptype))
        reboot()
        run("mkfs.ext4 /dev/vda{}".format(N+1))
    else:
        print "VDA3 partition seems to already exist"
        run("mkfs.ext4 /dev/vda{}".format(N))

    run("mkdir -p /data")
    mount_data()

