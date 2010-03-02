from os import system, chdir
from os.path import join
from shutil import rmtree, copytree

## Checkout

def system_echo(cmd):
    print cmd
    system(cmd)

class SVN:
    def __init__(self, url, rev):
        self.data = {'url':url, 'rev':rev}

    def checkout(self):
        system_echo('svn export %(url)s -r %(rev)d --force' % self.data)
        
class HG:
    # repository dir - dir under url to check out
    # dst - where to copy repository_dir
    def __init__(self, url, repository_dir, dst, rev):
        self.url = url
        self.repository_dir = repository_dir
        self.dst = dst
        self.rev = rev

    def checkout(self):
        slash = self.url.rstrip('/').rindex('/') + 1
        src = self.url[slash:]
        rmtree(src, ignore_errors=True)
        rmtree(self.dst, ignore_errors=True)

        system_echo('hg clone %s' % self.url)
        chdir(src)
        system_echo('hg up -r %s' % self.rev)
        chdir('..')
        copytree(join(src,self.repository_dir), self.dst)
        rmtree(src, ignore_errors=True)

class GIT:
    def __init__(self, url, folder, rev):
        self.url = url
        self.folder = folder
        self.rev = rev

    def checkout(self):
        base, app = self.folder.split('/')
        rmtree(base, ignore_errors=True)
        rmtree(app, ignore_errors=True)
        
        system_echo('git clone %s' % self.url)
        chdir(base)
        system_echo('git checkout %s' % self.rev)
        chdir('..')
        copytree(self.folder, app)
        rmtree(base, ignore_errors=True)

libs = (
#    SVN('http://code.djangoproject.com/svn/django/trunk/django', 11366),
#    SVN('http://django-tagging.googlecode.com/svn/trunk/tagging', 156),
#    SVN('http://django-voting.googlecode.com/svn/trunk/voting', 69),
#    SVN('http://django-simple-captcha.googlecode.com/svn/trunk/captcha', 33),
## These will delete svn data, so checking them out to _tmp directories and they have to be
## merged manually into proper directories.
## USe Unison to do it.
#    HG('http://bitbucket.org/ubernostrum/django-registration/', 'registration', '_tmp_registration', 'b360801eae96'),
#    HG('http://bitbucket.org/ubernostrum/django-profiles/', 'profiles', '_tmp_profiles', 'c21962558420'),
##    GIT('git://github.com/jezdez/django-robots.git', 'django-robots/_tmp_robots', '059c630'),
## This is now in mercurial here:
#    HG('http://bitbucket.org/jezdez/django-robots', 'robots', '_tmp_robots', 'a3644ec631af'),

# socialregistration requires pyfacebook
    GIT('git://github.com/sciyoshi/pyfacebook.git', 'pyfacebook/facebook', 'd4f516c'),
    GIT('git://github.com/flashingpumpkin/django-socialregistration.git', 'django-socialregistration/socialregistration', 'a129c63'),
#    SVN('http://django-facebookconnect.googlecode.com/svn/trunk', 50),

)

for lib in libs:
    lib.checkout()
