import os
from fabric.api import *


ENABLED = '/etc/nginx/sites-enabled'
AVAILABLE = '/etc/nginx/sites-available'

def install(start=True):
    # add nginx stable ppa
    sudo("add-apt-repository -y ppa:nginx/stable")
    sudo('aptitude update')
    sudo('aptitude -y install nginx')
    
    if start:
        nginx('start')

def dissite(site):
    """remove an enabled nginx site configuration link"""
    require('hosts')
    with settings(warn_only=True):
        return sudo('rm %s/%s' % (ENABLED, site))

def ensite(path, site):
    require('hosts')
    enabled = ENABLED
    with settings(warn_only=True):
        return sudo('ln -s %(path)s %(enabled)s/%(site)s' % locals())

def reload():
    return nginx('reload')

def restart():
    return nginx('restart')

def stop():
    return nginx('stop')

def start():
    return nginx('start')

def nginx(cmd):
    return sudo("/etc/init.d/nginx %s" % cmd)

