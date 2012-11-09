#!/usr/bin/env python


"""
Odekro deployment script
"""

import os, re , time
#, getpass, fileinput, shutil

from fabric.api import hide, settings, cd, env, prefix, put, get, require
from fabric.api import local, run, sudo

from fab import postgres as pg
from fab import server, nginx, webapp
import fab


env.local_root = os.path.abspath(os.path.dirname(__file__))

env.project = 'mzalendo'
env.git_remote = "origin"
env.git_branch = "master"
env.pip_requirements = 'requirements.txt'
env.local_settings = 'deploy/local_settings.py'
env.log_level = 'debug'

env.dbname = 'odekro'
env.dbuser = 'postgres'

env.webapp_user = 'odekro_webapp'
env.webapp_group = 'odekro_webapp'

env.basedir = '/var/www/%(project)s' % env
# env.basedir = '/var/www/%(project)s' % env


#env.shell = "/bin/sh -c"

def setup(dbuser=None, dbpassword=None):
    require('hosts', provided_by=[vm, staging, production])
    require('webapp_user')
    require('basedir')

    server.install_packages()
    server.create_webapp_user()
    
    postgres.install()

    try:
        pg.setup_postgis()
    except: pass

    setup_db()
    
    nginx.install()
    webapp.prepare()


def deploy(db=None, dbuser=None, dbpasswd=None, version=None, init='yes'):
    """Deploy latest version of the site (or a specific version to be made live)
        
    Deploy a version to the servers, install any required third party 
    modules, install the virtual host and then restart the webserver
    """
    require('hosts', provided_by=[dev, staging, production])
    require('basedir')
    require('webapp_user')
    require('git_branch')

    restart = False

    if not version:
        env.version = time.strftime('%Y%m%d%H%M%S')
        
        webapp.upload()
        webapp.install()

        if init is 'yes':
            webapp.init()

        restart = True
    else:
        #TODO check to see if version exists
        # env.version = version
        # _symlink_current_version()
        pass   

    if db and dbuser and dbpasswd:
        configure(db, dbuser, dbpasswd)

    if restart: 
        nginx.reload()
        webapp.start()
        

def rollback():
    pass


# ADHOC

def configure(db=env.dbname, dbuser=env.dbuser, password=''):
    setup_db(db, dbuser, password)
    configure_webapp(db, dbuser, password)

def setup_db(db=env.dbname, user=env.dbuser, password=''):
    if not pg.user_exists(user):
        pg.create_user(user, password)
    if not pg.database_exists(db):
        pg.create_database(db, user, 
                           template='template_postgis')

def configure_webapp(db=env.dbname, user=env.dbuser, password=''):
    env.version = 'current'
    webapp.configure(dbuser=user, dbpass=password, dbname=db)
    

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


def staging():
    pass

def production():
    env.hosts = ['208.68.37.14']
    env.user = 'root'
    env.domain = 'odekro.org'
    env.log_level = 'info'

 
