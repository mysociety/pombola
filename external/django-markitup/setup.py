from setuptools import setup
import subprocess
import os.path

try:
    # don't get confused if our sdist is unzipped in a subdir of some
    # other hg repo
    if os.path.isdir('.hg'):
        p = subprocess.Popen(['hg', 'parents', r'--template={rev}\n'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not p.returncode:
            fh = open('HGREV', 'w')
            fh.write(p.communicate()[0].splitlines()[0])
            fh.close()
except (OSError, IndexError):
    pass

try:
    hgrev = open('HGREV').read()
except IOError:
    hgrev = ''

long_description = (open('README.rst').read() +
                    open('CHANGES.rst').read() +
                    open('TODO.rst').read())

def _static_files(prefix):
    return [prefix+'/'+pattern for pattern in [
        'markitup/*.*',
        'markitup/sets/*/*.*',
        'markitup/sets/*/images/*.png',
        'markitup/skins/*/*.*',
        'markitup/skins/*/images/*.png',
        'markitup/templates/*.*'
    ]]

setup(
    name='django-markitup',
    version='1.0.0.post%s' % hgrev,
    description='Markup handling for Django using the MarkItUp! universal markup editor',
    long_description=long_description,
    author='Carl Meyer',
    author_email='carl@oddbird.net',
    url='http://bitbucket.org/carljm/django-markitup/',
    packages=['markitup', 'markitup.templatetags'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    zip_safe=False,
    test_suite='runtests.runtests',
    tests_require='Django>=1.3',
    package_data={'markitup': ['templates/markitup/*.html'] +
                              _static_files('static')}
)
