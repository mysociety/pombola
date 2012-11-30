from fabric.api import *
from fabric.contrib.files import exists
import os
import sys

import random

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

    if not exists('%(basedir)s/lib/python2.7/site-packages/gdal.py' % env):
        _install_gdal()
    if not exists('%(basedir)s/lib/libxapian.so' % env):
        _install_xapian()
    _install_pil()
    _install_gunicorn()


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

    previous = '%(basedir)s/releases/previous' % env
    current  = '%(basedir)s/releases/current' % env
    source   = '%(basedir)s/releases/%(version)s' % env

    _sudo(('rm %(previous)s; '
           'mv %(current)s %(previous)s; '
           'ln -s %(source)s %(current)s') % locals())


def configure(db=None, dbuser=None, dbpasswd=None, email_passwd='',
              dbhost='localhost', timezone='Africa/Accra'):
    """Create the general.yml configuration."""

    require('basedir')
    require('version')
    require('is_staging')

    if db is None:
        db = 'odekro'
    if dbuser is None:
        dbuser = 'postgres'
    if dbpasswd is None:
        dbpasswd = ''

    # TODO: move hardcoded values out of here to fabfile.py

    configs = (
        ('DB_USER', dbuser), 
        ('DB_NAME', db), 
        ('DB_PASS', dbpasswd), 
        ('DB_HOST', dbhost),
        ('TIME_ZONE', timezone),
        ('SECRET_KEY', _random_chars(50)),
        ('MANAGERS_EMAIL', 'managers@odekro.org'),
        ('MANAGERS_NAME', 'Odekro Managers'),
        ('TWITTER_ACCOUNT_NAME', 'odekro'),
        ('DISQUS_SHORTNAME', 'odekro'),
        ('GOOGLE_ANALYTICS_ACCOUNT', 'UA-36374336-1'),
        ('FACEBOOK_APP_ID', '342278959203828'),
        ('FACEBOOK_API_SECRET', 'b1508ccaed96bc4006e8f485257e3833'),
        ('TWITTER_CONSUMER_KEY', 'xPO8GPH9fJFvp89KnAtrZw'),
        ('TWITTER_CONSUMER_SECRET', 'jHYE0inEBMixgiQny1LltYenxWk5HUmTfM3E1hzzTYw'),
        # Email
        ('EMAIL_HOST', 'smtp.gmail.com'),
        ('EMAIL_HOST_USER', 'mailman@odekro.org'),
        ('EMAIL_HOST_PASSWORD', email_passwd or ''),
        ('STAGING', '1' if env.is_staging else '0')
    )

    configs2 = (
        ('COUNTRY_APP', 'odekro'),
        ('EMAIL_SETTINGS', 'true'),
        ('EMAIL_PORT', '587'),
        ('EMAIL_USE_TLS', 'true'),
        ('EXT_CONTEXT_PROCESSORS', '["odekro.context_processors.process"]')
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


def _install_pil():
    require('virtualenv')

    # install the build dependencies
    sudo('aptitude -y install build-dep python-imaging')
    # symlink the libraries

    for pkg in ('libfreetype', 'libjpeg', 'libz'):
        try:
            sudo('ln -s /usr/lib/`uname -i`-linux-gnu/%s.so /usr/lib/' % pkg)
        except: pass
    # install

    sudo('%(basedir)s/bin/pip install PIL' % env)

def _install_gdal():
    """Build and install GDAL into the virtualenv.
    More here: http://openblockproject.org/docs/install/common_install_problems.html
    """
    require('basedir')

    packages = (
        # 'postgresql-9.1-postgis', 
        'libgdal1', 
        'libgdal1-dev', 
        'build-essential',
        'python-dev'
    )
    sudo('aptitude install -y %s' % ' '.join(packages))
    sudo('ldconfig')

    with cd('%(basedir)s' % env):
        _sudo('source ./bin/activate')
        _sudo('./bin/pip install --no-install "%s"' % _gdal_pip_version())
        try:
            with cd('%(basedir)s/build/GDAL' % env):
                _sudo('rm -f setup.cfg')
                library_dirs, libraries, include_dirs = _gdal_configs()
                bin_python = '%(basedir)s/bin/python' % env
                _sudo(('%(bin_python)s setup.py build_ext'
                       ' --include-dirs=%(include_dirs)s '
                       ' --library-dirs=%(library_dirs)s '
                       ' --libraries=%(libraries)s') % locals())
        except: pass
        _sudo('./bin/pip install --no-download GDAL')

def _gdal_pip_version():
    version = sudo('gdal-config --version')[:3]
    m = version[0]
    n = version[2]
    o  = str(int(n) + 1)
    return 'GDAL>=%(m)s.%(n)s,<%(m)s.%(o)sa' % locals()

def _gdal_configs():
    import re
    res = sudo('gdal-config --libs')

    m = re.match('.*-L([^\s]+).*', res)
    if m:
        library_dirs = m.group(1)
    else:
        library_dirs = ''

    m = re.match('.*-l([^\s]+).*', res)
    if m:
        libraries = m.group(1)
    else:
        libraries = ''

    res = sudo('gdal-config --cflags')
    m = re.match('.*-I([^\s]+).*', res)
    if m:
        include_dirs = m.group(1)
    else:
        include_dirs = ''

    return (library_dirs, libraries, include_dirs)

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

    dest = '%(basedir)s/releases/%(version)s/conf/nginx.conf' % env
    src = '%s-template' % dest
    project_home = '%(basedir)s/releases/%(version)s/%(project)s' % env

    _sudo('cp %(src)s %(dest)s' % locals())
    
    env.project_home = project_home
    env.base_domain = '.'.join(env.domain.split('.')[-2:])

    configs = [('%%(%s)s' % k,  ('%%(%s)s' % k) % env) for k in \
               ['domain', 'project_home', 'base_domain', 
                'media_root', 'robots_dir']]
    # (
    #     ('%(domain)s', '%(domain)s' % env),
    #     ('%(project_home)s', project_home),
    #     ('%(naked_domain)s', '%(naked_domain)s' % env),
    #     ('%(media_root)s', '%(media_root)s' % env),
    # )
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
    with prefix('PATH=%(basedir)s/bin/:PATH' % env):
        return _sudo(cmd)

def _sudo(cmd):
    require('webapp_user')
    return sudo(cmd, user='%(webapp_user)s' % env)
