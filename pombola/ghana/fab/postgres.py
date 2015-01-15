"""
PostgreSQL users and databases
==============================

This module provides tools for creating PostgreSQL users and databases.

"""
from __future__ import with_statement

import re

from fabric.api import *
from fabric.contrib.files import exists


def setup_postgis():
    require('hosts')
    try:
        install_postgres()
    except: pass

    install_postgis()
    configure_postgis()

def install_postgres():
    require('hosts')
    sudo('aptitude install -y postgresql postgresql-server-dev-9.1')

def install_postgis():
    require('hosts')
    require('basedir')

    VERSION = '1.5.7'
    REP = 'http://download.osgeo.org/postgis/source'
    pkg = 'postgis-%s' % VERSION
    tar = '%s.tar.gz' % pkg

    _install_postgis_deps()

    with cd('%(basedir)s/packages' % env):
        if not exists(tar):
            _sudo('wget %s/%s' % (REP, tar))
        if not exists(pkg):
            _sudo('tar xzf %s' % tar)
        with cd(pkg):
            sudo('ldconfig')
            _sudo('./configure && make')
            sudo('make install')

def configure_postgis(password=None):
    v = postgres_version()
    if v:
        gis_v = postgis_version(v)
        contrib = '/usr/share/postgresql/%s/contrib/postgis-%s' % (v[:3], gis_v)
        for cmd in (
            '''psql -c "CREATE ROLE gisgroup;"''',
            '''createdb -E UTF8 template_postgis''',
            '''psql -d template_postgis < %s/postgis.sql''' % contrib,
            '''psql -d template_postgis < %s/spatial_ref_sys.sql''' % contrib,
            '''psql -c "ALTER TABLE geometry_columns OWNER TO gisgroup;" template_postgis''',
            '''psql -c "ALTER TABLE spatial_ref_sys OWNER TO gisgroup;" template_postgis'''):
            _run(cmd, password)

def create_user(name, password, groups=None, encrypted=True):
    """
    Create a PostgreSQL user.

    Example::

        # Create DB user if it does not exist
        if not user_exists('dbuser'):
            create_user('dbuser', password='somerandomstring')

    """
    if encrypted:
        with_password = 'WITH ENCRYPTED PASSWORD'
    else:
        with_password = 'WITH PASSWORD'

    if groups:
        groups = ' IN GROUP %s' % ', '.join(groups)
    else:
        groups = ''

    _run('''psql -c "CREATE USER %(name)s %(with_password)s '%(password)s'%(groups)s;"''' % locals())


def create_database(name, owner, template='template0', encoding='UTF8', locale='en_US.UTF-8'):
    """
    Create a PostgreSQL database.

    Example::

        # Create DB if it does not exist
        if not database_exists('myapp'):
            create_database('myapp', owner='dbuser')

    """
    _run('''createdb --owner %(owner)s --template %(template)s --encoding=%(encoding)s\
 --lc-ctype=%(locale)s --lc-collate=%(locale)s %(name)s''' % locals())


def user_exists(name):
    """
    Check if a PostgreSQL user exists.
    """
    with settings(hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True):
        res = _run('''psql -t -A -c "SELECT COUNT(*) FROM pg_user WHERE usename = '%(name)s';"''' % locals())
    return (res == "1")


def change_password(name, password, encrypted=True):
    if encrypted:
        with_password = 'WITH ENCRYPTED PASSWORD'
    else:
        with_password = 'WITH PASSWORD'
    cmd = '''psql -c "ALTER USER %(name)s %(with_password)s '%(password)s';"''' % locals()
    _run(cmd)


def database_exists(name):
    """
    Check if a PostgreSQL database exists.
    """
    with settings(hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True):
        return _run('''psql -d %(name)s -c ""''' % locals()).succeeded

def unconfigure_postgis(password=None):
    v = postgres_version()
    if v:
        gis_v = postgis_version(v)
        contrib = '/usr/share/postgresql/%s/contrib/postgis-%s' % (v[:3], gis_v)
        _run('''psql -d template_postgis < %s/uninstall_postgis.sql''' % contrib, password)

def postgis_version(ver=None):
    if not ver:
        ver = postgres_version()
    else:
        ver = str(ver)
    contrib = '/usr/share/postgresql/%s/contrib' % ver[:3]
    out = qrun('find %s -iname "postgis-*"' % contrib)
    return out.replace('%s/postgis-' % contrib, '')

def postgres_version():
    require('hosts')
    out = qrun('psql --version')
    s = out.split('\n')[0]
    m = re.match('.+(\d+)\.(\d+)\.(\d+).*', s)
    if m:
        return '%s.%s.%s' % (m.group(1), m.group(2), m.group(3))
    return ''

def warn_only():
    return settings(hide('running', 'stdout', 'stderr', 'warnings'), 
                    warn_only=True)

def qrun(cmd):
    with warn_only():
        return run(cmd)

def _install_postgis_deps():
    sudo('aptitude install -y libproj-dev')

def _run(command, password=None):
    """
    Run command as 'postgres' user
    """
    with cd('/var/lib/postgresql'):
        if password:
            password = 'PGPASSWORD=%s; ' % password
        else:
            password = ''
        return sudo('%ssudo -u postgres %s' % (password, command))

def _sudo(cmd):
    require('webapp_user')
    return sudo(cmd, user='%(webapp_user)s' % env)

