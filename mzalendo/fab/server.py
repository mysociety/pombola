from fabric.api import *

def add_ssh_key(path, password=None, user=None):
    require('hosts')
    if password:
        env.password = password
    if user:
        env.user = user

    tmp_key = os.path.join('/tmp', os.path.basename(path))
    authorized_keys2 = '$HOME/.ssh/authorized_keys2'
    
    put(path, tmp_key)
    with settings(hide('running', 'stdout', 'stderr', 'warnings'), 
                  warn_only=True):
        run(('mkdir $HOME/.ssh; '
             'chmod 0700 $HOME/.ssh'))
    run('cat %s >> %s' % (tmp_key, authorized_keys2))
    run('rm %s' % tmp_key)
    run('chmod 0600 %s' % authorized_keys2)

def install_packages():
    """Installs the required packages"""
    require('hosts')

    packages = (
        # python and build essensials
        'build-essential',
        'bcrypt',
        'python-dev',
        'python-pip',
        'python-virtualenv',
        'python-software-properties',
        # "supervisor",

        # for mapit
        #| libgdal1-1.5.0
        # 'libgdal1-1.6.0',
        'gdal-bin',
        'libgdal-dev',
        # 'libgdal1',
        # 'libgdal1-dev',
        'python-gdal',

        # Xapian search engine
        # 'libxapian22',

        # probably installed as requirement for others
        'libjpeg',
        
        # Some dependencies in requirements.txt are listed as repos
        # so we need the various repo management tools to fetch them.
        'mercurial',
        'git-core',

        # May as well use the Debian maintained versions.
        # 'python-docutils',
        # 'python-bcrypt',
        # 'python-xapian',
        # 'python-markdown',
        # 'python-yaml',
        # 'python-openid',
        # 'python-beautifulsoup',
        # 'python-dateutil',
    )

    # for gdal
    # TODO: determine if repository already added
    sudo('apt-add-repository -y ppa:ubuntugis/ubuntugis-unstable')
    # sudo('apt-add-repository -y ppa:xapian-backports/xapian-1.2')

    try:
        sudo('aptitude update')
    except: pass
    
    sudo('aptitude -y install %s' % ' '.join(packages))
    
def create_webapp_user():
    """Create a user for gunicorn, celery, etc."""
    require('hosts')
    require('webapp_user')
    try:
        sudo('useradd --system %(webapp_user)s' % env)
    except: pass


