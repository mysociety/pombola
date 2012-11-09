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
        ctl('start')

def dissite(site):
    """remove an enabled nginx site configuration link"""
    require('hosts')
    with settings(warn_only=True):
        return sudo('rm %s/%s' % (ENABLED, site))

def ensite(path, site=''):
    require('hosts')
    with settings(warn_only=True):
        with cd(ENABLED):
            return sudo('ln -s %(path)s %(site)s' % locals())

def reload():
    return ctl('reload')

def restart():
    return ctl('restart')

def stop():
    return ctl('stop')

def start():
    return ctl('start')

def ctl(cmd):
    if cmd in ['start', 'stop', 'reload', 'restart', 'status']:
        return sudo("/etc/init.d/nginx %s" % cmd)

