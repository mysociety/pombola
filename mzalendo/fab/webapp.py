from fabric.api import *
from fabric.contrib.files import exists
import os
import sys

import random; 

CHARS = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*(-_=+)"

def prepare():
    """Setup a fresh virtualenv as well as a few useful directories
    """
    require('hosts')
    require('basedir')
    require('webapp_user')
    #TODO check existence of env first
    sudo(('mkdir -p %(basedir)s/releases; '
          'mkdir -p %(basedir)s/shared; '
          'mkdir -p %(basedir)s/packages; '
          'virtualenv --python=python2.7 %(basedir)s; ') % env)
    with cd('%(basedir)s' % env):
        sudo('chown -R %(webapp_user)s:%(webapp_user)s .' % env)

def upload(rm_local=True):
    """Create an archive from the current Git master branch and upload it."""
    require('version')
    require('basedir')
    require('project')    
    require('git_branch')
    require('local_root')

    filename = '%(version)s.tar.gz' % env
    
    path = os.path.abspath(os.path.join(env.local_root, '../'))
    _archive(env.git_branch, filename, path)
    tarfile = os.path.join(path, filename)

    put('%s' % tarfile, 
        '%(basedir)s/packages/' % env, use_sudo=True)
    if rm_local:
        local('rm %s' % tarfile)
    _unpack()

def install(db=None, dbuser=None, dbpasswd=None):
    require('version')
    require('basedir')
    require('project')
    require('pip_requirements')

    _install_gdal()
    _install_xapian()
    _install_gunicorn()
    _install_requirements()
    _configure_gunicorn()
    _configure_upstart()
    _configure_nginx()
    link_current_version()

def init():
    """Initialize the db from Django."""
    require('basedir')
    require('project')

    with cd('%(basedir)s/releases/current/%(project)s' % env):
         with prefix('PATH=%(basedir)s/bin/:PATH' % env):
            _sudo('python manage.py syncdb --noinput --verbosity=1')
            _sudo('python manage.py migrate --verbosity=1')
            _sudo('python manage.py collectstatic --noinput')

def start():
    """Start the web app server."""
    ctl('start')

def stop():
    """Stop the web app server."""
    ctl('stop')

def status():
    """Show the status of the upstart process for Odekro."""
    ctl('status')

def restart():
    """Restart the web app server."""
    ctl('stop')
    ctl('start')

def ctl(cmd):
    if cmd in ['start', 'stop', 'status']:
        sudo('%s odekro' % cmd)


def link_current_version():
    """Symlink the current live version of the web app."""
    require('version')
    require('basedir')

    _sudo(('rm %(basedir)s/releases/previous; '
           'mv %(basedir)s/releases/current %(basedir)s/releases/previous; '
           'ln -s %(basedir)s/releases/%(version)s %(basedir)s/releases/current') % env)


def configure(db=None, dbuser=None, dbpasswd=None, 
              dbhost='localhost', timezone='Africa/Accra'):
    """Create the general.yml configuration."""

    require('basedir')
    require('version')

    if db is None:
        db = 'odekro'
    if dbuser is None:
        dbuser = 'postgres'
    if dbpasswd is None:
        dbpasswd = ''

    configs = (
        ('DB_USER', dbuser), 
        ('DB_NAME', db), 
        ('DB_PASS', dbpasswd), 
        ('DB_HOST', dbhost),
        ('TIME_ZONE', timezone),
        ('SECRET_KEY', _random_chars(50))
    )

    configs2 = (
        ('COUNTRY_APP', 'kenya'),
    )

    path = '%(basedir)s/releases/%(version)s/conf/general.yml' % env
    
    try:
        _sudo('rm %s' % path)
    except: pass
    
    _sudo('cp %s-example %s' % (path, path))

    def __sed(st, configs, path):
        s = ';'.join([st % (key, key, val) for key, val in configs])
        return _sed(s, path)  

    __sed("s|%s: '[^\']*'|%s: '%s'|", configs, path)
    __sed("s|%s: .*|%s: %s|", configs2, path)

def _archive(branch, filename, path='', prefix='', format='tar'):
    """Create an archive of the web app from git."""
    if prefix:
        prefix = '--prefix=%s' % prefix

    cmd = ('cd  %(path)s; '
           'git archive --format=%(format)s '
           '%(prefix)s %(branch)s | '
           'gzip > %(filename)s') % locals()
    return local(cmd)

def _unpack():
    """Unpack an archive in the packages folder into the releases folder."""
    require('version')
    require('basedir')
    _sudo('mkdir %(basedir)s/releases/%(version)s' % env)
    _sudo(('tar zxf %(basedir)s/packages/%(version)s.tar.gz -C '
         '%(basedir)s/releases/%(version)s') % env)

def _install_requirements():
    """Install the required packages from the requirements file using pip."""
    require('version')
    require('basedir')
    require('project')
    require('pip_requirements')


    with cd('%(basedir)s' % env):
        _sudo('source ./bin/activate')
        _sudo(('./bin/pip install -r '
               './releases/%(version)s/%(pip_requirements)s') % env)


def _install_gdal():
    """Build and install GDAL into the virtualenv."""
    require('basedir')
    with cd('%(basedir)s' % env):
        _sudo('source ./bin/activate')
        _sudo('./bin/pip install --no-install GDAL')
        try:
            with cd('%(basedir)s/build/GDAL' % env):
                _sudo(('%(basedir)s/bin/python setup.py build_ext'
                       ' --include-dirs=/usr/include/gdal/') % env)
        except: pass
        _sudo('./bin/pip install --no-download GDAL')


def _install_xapian(version='1.2.12'):
    """Install Xapian into the virtual env."""
    # Thanks to https://gist.github.com/199025
    require('basedir')

    sudo('aptitude install -y zlib1g-dev g++')

    REP = 'http://oligarchy.co.uk/xapian/%s/' % version

    with cd('%(basedir)s' % env):
        _sudo('source ./bin/activate')
        # _sudo('export VENV=$VIRTUAL_ENV')
        with cd ('%(basedir)s/packages' % env):
            for pkg in ('core', 'bindings'):
                tarfile = 'xapian-%s-%s.tar.gz' % (pkg, version)
                if not exists(tarfile):
                    _sudo('wget %s/%s' % (REP, tarfile))
                if not exists('xapian-%s-%s' % (pkg, version)):
                    _sudo('tar xzvf %s' % tarfile)
        with cd('%s/packages/xapian-core-%s' % (env.basedir, version)):
            _sudo(('PYTHON=%(basedir)s/bin/python '
                   './configure --prefix=%(basedir)s && '
                   'make && '
                   'make install' % env))

        _sudo('export LD_LIBRARY_PATH=%(basedir)s/lib' % env)
        
        # http://trac.xapian.org/ticket/409

        with cd('%s/packages/xapian-bindings-%s' % (env.basedir, version)):
            _sudo(('PYTHON=%(basedir)s/bin/python '
                   'LD_LIBRARY_PATH=%(basedir)s/lib '
                   './configure XAPIAN_CONFIG=%(basedir)s/bin/xapian-config '
                   '--prefix=%(basedir)s --with-python && '
                   'make && '
                   'make install') % env)

def _install_gunicorn():
    """Install gunicorn into web app virtualenv, even if available globally.
    
    More details here: https://github.com/benoitc/gunicorn/pull/280 
    """
    _vsudo('pip install -I gunicorn')

def _configure_gunicorn(user=None, group=None):
    """Configure the gunicorn startup script and copy to the app bin folder."""
    require('version')
    require('basedir')
    require('webapp_user')
    require('webapp_group')
    require('log_level')

    if not user:
        user = env.webapp_user
    if not group:
        group = env.webapp_group

    fname = 'start_gunicorn.sh'
    project_home = '%(basedir)s/releases/%(version)s' % env

    src = '%(project_home)s/conf/%(fname)s-template' % locals()
    dest = '%(project_home)s/bin/%(fname)s' % locals()

    _sudo('cp %(src)s %(dest)s' % locals())
    
    configs =  (
        ('%(webapp_user)s', user),
        ('%(webapp_group)s', group),
        ('%(project_home)s', project_home),
        ('%(virtualenv)s', env.basedir),
        ('%(log_level)s', env.log_level or 'debug')
    )
    # s = ';'.join(["s|%s|%s|" % (s, r) for s, r in configs])
    _sed2(configs, dest)
    _sudo('chmod +x %(dest)s' % locals())

        
def _configure_upstart():
    """Configure the upstart script and copy to /etc/init."""
    require('version')
    require('basedir')

    dest = '%(basedir)s/releases/%(version)s/conf/upstart.conf' % env
    src = '%s-template' % dest
    _sudo('cp %(src)s %(dest)s' % locals())

    configs = (
        ('%(basedir)s', '%(basedir)s' % env),
        ('%(version)s', '%(version)s' % env)
    )
    # s = ';'.join(["s|%s|%s|" % (s, r) for s, r in configs])
    _sed2(configs, dest)
    sudo('mv %(dest)s /etc/init/odekro.conf' % locals())

def _configure_nginx():
    require('version')
    require('basedir')
    require('domain')

    dest = '%(basedir)s/releases/%(version)s/conf/nginx.conf'
    src = '%s-template' % dest

    _sudo('cp %(src)s %(dest)s')
    configs = (
        ('%(domain)s', '%(domain)s' % env),
        ('%(project_home)s', '%(project_home)s' % env)
    )
    _sed2(configs, dest)

def _random_chars(size):
    """Generates a string of random characters."""
    return "".join([random.choice(CHARS) for i in range(size)])

def _sed2(pairs, dest):
    return _sed(';'.join(["s|%s|%s|" % (s, r) for s, r in pairs]), dest)

def _sed(s, filepath):
    """Perform in-place replacement (with sed) on the supplied file path."""
    cmd = '''sed %s-e "%s" %s %s'''
    try:
        _sudo(cmd % ('-i ', s, '', filepath)) # GNU
    except:
        _sudo(cmd % ('', s, '-i ""', filepath)) # BSD

def _vsudo(cmd):
    # activate = 'source %(basedir)s/bin/activate' % env
    # return _sudo('%s && %s' % (activate , cmd))
    with prefix('PATH=%(basedir)s/bin/:PATH' % env):
        return _sudo(cmd)

def _sudo(cmd):
    require('webapp_user')
    return sudo(cmd, user='%(webapp_user)s' % env)
