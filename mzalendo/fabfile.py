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

env.dbname = 'odekro'
env.dbuser = 'postgres'

env.webapp_user = 'odekro_webapp'

env.basedir = '/var/www/%(project)s' % env


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
    # supervisord install
    #
    webapp.prepare()


def setup_db(user=env.dbuser, password='', db=env.dbname):
    if not pg.user_exists(user):
        pg.create_user(user, password)
    if not pg.database_exists(db):
        pg.create_database(db, user, 
                           template='template_postgis')    
    


def conf_webapp(user=env.dbuser, password='', db=env.dbname):
    env.version = 'current'
    webapp.configure(dbuser=user, dbpass=password, dbname=db)


def deploy(version=None, init='yes'):
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
        
        # if updating is 'yes':
        #     deactivate_application()
        
        webapp.upload()
        webapp.install()

        if init is 'yes':
            webapp.init()

        # upload gunicorn script
        # upload nginx conf
        # upload supervisord conf

        restart = True
    else:
        #TODO check to see if version exists
        # env.version = version
        # _symlink_current_version()
        pass   

    if restart: 
        nginx.restart()
        supervisor.restart()


def rollback():
    pass




    

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
    env.basedir = '/var/www/%(project)s' % env


def staging():
    pass

def production():
    env.hosts = ['root@208.68.37.14']
    env.domain = 'odekro.org'
    env.basedir = '/var/www/%(project)s' % env
    env.rapidsms_conf = 'deploy/rapidsms-router.conf'
    env.fixtures = 'deploy/fixtures.json'
    env.wsgi_file = 'deploy/wsgi.py'
    env.vhost_file = 'deploy/apache.conf'
    env.apache_sites = '/etc/apache2/sites-available'

 
