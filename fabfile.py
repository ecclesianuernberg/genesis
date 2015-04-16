from fabric.api import *


env.user = 'root'
env.hosts = ['ecclesianuernberg.de']
env.git_remote_name = 'deploy'
env.repo_dir = '/srv/git/genesis'
env.app_dir = '/srv/www/genesis'
env.app_user = 'www-data'


def tox():
    ''' running local tox'''
    local('tox')


def git():
    # push devel branch to master branch on server
    local('git push {} devel:master'.format(env.git_remote_name))

    with cd(env.repo_dir):
        # checkouts in a different work tree aka the app directory
        run('GIT_WORK_TREE="{}" git checkout -f master'.format(env.app_dir))

        # set HEAD back do devel so you can push again
        run('git symbolic-ref HEAD refs/heads/devel')


def install_app():
    with cd(env.app_dir):
        # create virtualenv
        run('virtualenv env')

        # install deps
        run('env/bin/pip install -r requirements.txt')

        # change permissions for all files
        run('chown -Rv {}:{} {}'.format(env.app_user,
                                        env.app_user,
                                        env.app_dir))

        # upgrade db
        run('env/bin/python manage.py db upgrade')


def reload_apache():
    run('service apache2 reload')


def deploy():
    tox()
    git()
    install_app()
    reload_apache()
