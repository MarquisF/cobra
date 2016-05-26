#!/usr/bin/env python
#
# Copyright 2016 Feei. All Rights Reserved
#
# Author:   Feei <wufeifei@wufeifei.com>
# Homepage: https://github.com/edge-security/cobra
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the file 'doc/COPYING' for copying permission
#

import os
import subprocess
import ConfigParser
from urllib import quote

from utils import log

"""
usage and example.

#!/usr/bin/env python
from pickup.GitTools import Git
repo_address = 'your repo address here'

# create a git object.
gg = Git(repo_address, 'your username here', 'your password here')

# use get_repo() method to clone the repo, if already cloned, it will pull the latest version.
gg.get_repo()

# you can also call the special method manually.
# clone() will clone the repo to local.
# pull() will pull the local repo to the latest version.
# gg.clone()
# gg.pull()

# diff(new_version, old_version, raw_output) method will diff the two version.
# and return the diff result in str.
diff_result = gg.diff('ef8ab030a54e3', '4640bc08a08f4')
print diff_result

# the third param "raw_output" will control the return format. default is False.
# If it set True, it will return the "git diff" raw output, if it set to False (default is False),
# it will return a dict which stores the formatted increment content.
#
# example output
# {'bb.txt': ['hhhhhhh'], 'aa.txt': ['ccccc', 'ddddd']}
# bb.txt add a line, the content is 'hhhhhhh'.
# aa.txt add two line, the content is 'ccccc' and 'ddddd'.
"""


class Git:
    """
    A Git class.
    You can clone, pull, diff the repo via this class.

    repo_address: the repo's url
    repo_directory: the repo's local path
    repo_username: the username for the repo's url
    repo_password: the password for the repo's password
    """

    repo_address = None
    repo_directory = None
    repo_username = None
    repo_password = None

    # https://github.com/<username>/<reponame>

    def __init__(self, repo_address, username, password):
        config = ConfigParser.ConfigParser()
        config.read('config')
        self.upload_directory = config.get('cobra', 'upload_directory') + os.sep
        self.repo_address = repo_address
        self.repo_username = username
        self.repo_password = password
        repo_user = self.repo_address.split('/')[-2]
        repo_name = self.repo_address.split('/')[-1]
        if '.git' not in repo_name:
            self.repo_address += '.git'
        else:
            repo_name = repo_name.split('.')[0]

        self.repo_directory = self.upload_directory + repo_user + '_' + repo_name

        log.info('Git class init.')

    def pull(self):
        """Pull a repo from repo_address and repo_directory"""
        log.info('start pull repo')

        # change work directory to the repo
        current_dir = os.getcwd() + os.sep
        repo_dir = current_dir + self.repo_directory
        os.chdir(repo_dir)

        cmd = 'git pull'
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        (pull_out, pull_err) = p.communicate()
        log.info(pull_out)

        # change work directory back.
        os.chdir(current_dir)

        if 'Updating' in pull_out or 'up-to-date' in pull_out:
            log.info('pull done.')
            return True
        else:
            return False

    def clone(self):
        """Clone a repo from repo_address
        :return: True - clone success, False - clone error.
        """
        log.info('start clone repo')
        clone_address = self.repo_address.split('://')[0] + '://' + quote(self.repo_username) + '@' + \
                        self.repo_address.split('://')[1]

        # clone repo with username and password
        # "http[s]://username:password@gitlab.com/username/reponame"
        # if add password in the url, .git/config will log your url with password
        # so only set username in the url, and echo password to "git clone"
        # "echo password | git clone http[s]://username@gitlab.com/username/reponame"
        cmd = 'echo "' + quote(self.repo_password) + '" | ' + 'git clone ' + \
              clone_address + ' "' + self.repo_directory + '"'

        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        (clone_out, clone_err) = p.communicate()
        log.info(clone_err)

        if 'not found' in clone_err or 'Not found' in clone_err:
            log.info("repo doesn't exist.")
            return False
        elif 'already exists' in clone_err:
            log.info("repo has already cloned.")
            return False
        else:
            log.info('clone done.')
            return True

    def diff(self, new_version, old_version, raw_output=False):
        """
        Diff between two version, in SHA hex.
        :param new_version: the new version in SHA hex.
        :param old_version: the old version in SHA hex.
        :param raw_output: True-return raw git diff result, False-return parsed result, only add content
        :return: the diff result in str, raw or formatted.
        """

        # change the work directory to the repo.
        current_dir = os.getcwd() + os.sep
        repo_dir = current_dir + self.repo_directory
        os.chdir(repo_dir)

        cmd = 'git diff ' + old_version + ' ' + new_version
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        (diff_out, diff_err) = p.communicate()
        log.info(diff_out)

        # change the work directory back.
        os.chdir(current_dir)
        log.info('diff done.')
        if raw_output:
            return diff_out
        else:
            return self.__parse_diff_result(diff_out)

    def __check_exist(self):
        """check if the repo has already cloned.
        :returns bool
            True : the repo already exist.
            False : the repo do not exist.
        """
        if os.path.isdir(self.repo_directory):
            return True
        else:
            return False

    def __parse_diff_result(self, content):
        """parse git diff output, return the format result
        :return: a dict, each key is the filename which has changed.
                 each value is a list store every changes.
        example:
                {'bb.txt': ['hhhhhhh'], 'aa.txt': ['ccccc', 'ddddd']}
                bb.txt add a line, the content is 'hhhhhhh'.
                aa.txt add two line, the content is 'ccccc' and 'ddddd'.
        """
        result = {}
        content = content.split('\n')
        tmp_filename = ''
        for x in content:
            if x != '' and x[0:3] == '+++':
                tmp_filename = x.split('/')[-1]
                result[tmp_filename] = []
            elif x != '' and x[0] == '+':
                if x[1:] != '':
                    result[tmp_filename].append(x[1:])

        return result

    def get_repo(self):
        """
        clone or pull the special repo.
        If the repo already exist in the "uploads" folder, it will pull the repo.
        If there is no repo in "uploads" folder, it will clone the repo.
        :return:
        """
        if self.__check_exist():
            log.info('repo already exist. Try to pull the repo')
            return self.pull()
        else:
            return self.clone()

    def __repr__(self):
        return "<Git - %r@%r>" % (self.repo_username, self.repo_address)