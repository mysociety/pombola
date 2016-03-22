import os.path

from fabric.api import env, hide, put, require, run, settings, sudo
from fabric.contrib.files import exists


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
        if not exists('$HOME/.ssh'):
            run(('mkdir $HOME/.ssh; '
                 'chmod 0700 $HOME/.ssh'))
        if not exists(authorized_keys2):
            run(('touch %(authorized_keys2)s; '
                 'chmod 0600 %(authorized_keys2)s') % locals())
        run('cat %s >> %s' % (tmp_key, authorized_keys2))
        run('rm %s' % tmp_key)

def install_packages():
    """Installs the required packages"""
    require('hosts')

    python_essentials = (
        # python and build essensials
        #'build-essential',
        #'bcrypt',
        'python-dev',
        'python-pip',
        'python-virtualenv',
        'python-software-properties',
    )


    packages = (
        "supervisor",
        #'gdal-bin',

        'libgdal-dev',
        # 'libgdal1',
        # 'libgdal1-dev',
        'python-gdal',

        # probably installed as requirement for others
        'libjpeg-dev',
        'libxml2-dev',
        'libxslt1-dev',

        # Some dependencies in requirements.txt are listed as repos
        # so we need the various repo management tools to fetch them.
        'openjdk-7-jre-headless',
        'git-core',
        'yui-compressor',
        'poppler-utils',
        'antiword',
        'rubygems',
    )

    gems = (
        'sass',
        'compass',
        'yui-compressor',
        )

    try:
        sudo('aptitude update')
    except: pass
    sudo('aptitude -y install %s' % ' '.join(python_essentials))


    # for gdal
    # TODO: determine if repository already added
    #sudo('apt-add-repository -y ppa:ubuntugis/ubuntugis-unstable')
    try:
        sudo('aptitude update')
    except: pass


    sudo('aptitude -y install %s' % ' '.join(packages))
    sudo('gem install %s' % ' '.join(gems))
    #symbolic links to sass and compass for env to work on debian
    sudo("ln -s /usr/local/bin/sass /usr/bin/sass")
    sudo("ln -s /usr/local/bin/compass /usr/bin/compass")
    install_elasticsearch()

def create_webapp_user():
    """Create a user for gunicorn, celery, etc."""
    require('hosts')
    require('webapp_user')
    try:
        sudo('useradd --system %(webapp_user)s' % env)
    except: pass

def install_elasticsearch():
    """ Download and install elasticsearch """
    require('hosts')
    try:
      sudo('wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.5.0.deb')
      sudo('dpkg -i elasticsearch-1.5.0.deb')
      sudo('rm elasticsearch-1.5.0.deb')
    except:pass
