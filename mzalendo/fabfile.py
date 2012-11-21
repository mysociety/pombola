#!/usr/bin/env python


"""
Odekro deployment script
"""

import os, re , time
#, getpass, fileinput, shutil

from fabric.api import hide, settings, cd, env, prefix, put, get, require
from fabric.api import local, run, sudo
from fabric.contrib.files import exists

from fab import postgres as pg
from fab import server, nginx, webapp
import fab


env.local_root = os.path.abspath(os.path.dirname(__file__))

env.project = 'mzalendo'
env.git_remote = "origin"
env.git_branch = "odekro"
env.pip_requirements = 'requirements.txt'
env.local_settings = 'deploy/local_settings.py'
env.log_level = 'debug'

env.dbname = 'odekro'
env.dbuser = 'postgres'

env.webapp_user = 'odekro_webapp'
env.webapp_group = 'odekro_webapp'

env.basedir = '/var/www/%(project)s' % env
env.virtualenv = env.basedir


#env.shell = "/bin/sh -c"

def clean():
    require('hosts', provided_by=[vm, staging, production])
    require('basedir')
    require('virtualenv')
    
    try:
        webapp.stop()
    except: pass
    
    try:
        sudo('rm -fr %(basedir)s' % env)
    except: pass


def setup():
    require('hosts', provided_by=[vm, staging, production])
    require('webapp_user')
    require('basedir')
    require('virtualenv')
    
    try:
        webapp.stop()
    except: pass

    prepare()

    setup_postgis()
    setup_db()
    
    if not exists('/etc/init.d/nginx'):
        nginx.install()

def prepare():
    require('hosts')
    require('webapp_user')

    server.install_packages()    
    server.create_webapp_user()
    webapp.prepare()

def setup_postgis():    
    require('hosts', provided_by=[vm, staging, production])
    require('basedir')
    require('virtualenv')

    try:
        # install postgres and postgis
        pg.setup_postgis()
    except: pass



def deploy(db=None, dbuser=None, dbpasswd=None, version=None, init='yes'):
    """Deploy latest version of the site (or a specific version to be made live)
        
    Deploy a version to the servers, install any required third party 
    modules, install the virtual host and then restart the webserver
    """
    require('hosts', provided_by=[vm, staging, production])
    require('basedir')
    require('virtualenv')
    require('webapp_user')
    require('git_branch')

    restart = False

    try:
        webapp.stop()
    except: pass

    if not version:
        env.version = time.strftime('%Y%m%d%H%M%S')
        
        webapp.upload()
        webapp.install()

        if db and dbuser and dbpasswd:
            configure(db, dbuser, dbpasswd)

        if init is 'yes':
            webapp.init()

        # ensite nginx.conf -> odekro
        try:
            nginx.dissite('default')
        except: pass

        try:
            nginx.dissite('odekro')
        except: pass
        
        nginx.ensite('%(basedir)s/releases/%(version)s/conf/nginx.conf' % env,
                     'odekro')

        restart = True
    else:
        #TODO check to see if version exists
        # env.version = version
        # _symlink_current_version()
        pass   


    if restart: 
        nginx.reload()
        webapp.start()

def init():
    webapp.init()


def rollback():
    pass

def app(cmd):
    webapp.ctl(cmd)


def setup_info_pages():
    pass


def manage_py(cmd, version='current'):
    require('basedir')
    require('project')

    basedir = env.basedir
    project = env.project
    virtualenv = basedir

    with cd ('%(basedir)s/releases/%(version)s/%(project)s' % locals()):
        webapp._sudo(('source %(virtualenv)s/bin/activate && '
                      '%(virtualenv)s/bin/python manage.py %(cmd)s') % locals())


# ADHOC

def configure(db=env.dbname, dbuser=env.dbuser, dbpasswd=''):
    setup_db(db, dbuser, dbpasswd)
    configure_webapp(db, dbuser, dbpasswd)

def setup_db(db=env.dbname, dbuser=env.dbuser, dbpasswd=''):
    if not pg.user_exists(dbuser):
        pg.create_user(dbuser, dbpasswd, groups=['gisgroup'])
    if not pg.database_exists(db):
        pg.create_database(db, dbuser, template='template_postgis')

def configure_webapp(db=env.dbname, dbuser=env.dbuser, dbpasswd=''):
    env.version = 'current'
    webapp.configure(db=db, dbuser=dbuser, dbpasswd=dbpasswd)


# ENVIRONMENTS
def dev():
    """local machine."""
    env.hosts = ['0.0.0.0']

def vm():
    """Local VMware test server.

    Specs: RAM - 512 MB
           HDD - 64bit 20 GB 
    """
    env.hosts = ['192.168.167.134']
    env.user = 'dev'
    env.domain = 'odekro.vm'
    env.log_level = 'debug'

def ian_vm():
    """Local VirtualBox test server.

    Specs: RAM - 512 MB
           HDD - 64bit 20 GB 
    """
    env.hosts = ['127.0.0.1']
    env.port = 2233
    env.user = 'idesouza'
    env.domain = 'odekro.vm'
    env.log_level = 'debug'

def vm2():
    """Local VMware test server.

    Specs: RAM - 512 MB
           HDD - 64bit 20 GB 
    """
    env.hosts = ['192.168.167.135']
    env.user = 'dev'
    env.domain = 'odekro.vm'
    env.log_level = 'debug'


def staging():
    pass

def production():
    env.hosts = ['208.68.37.14']
    env.user = 'root'  #we need a new user for this; root can't ssh
    env.domain = 'odekro.org'
    env.log_level = 'info'

 
