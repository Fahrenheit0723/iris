# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


import datetime
import logging
import os
import shutil
import tempfile
import git
from src.core.api.arg_parser import parse_args
from src.core.api.os_helpers import OSHelper

logger = logging.getLogger(__name__)


def __create_tempdir():
    """Creates the temporary directory.
    Writes to the global variable tmp_dir
    :return:
         Path of temporary directory.
    """
    temp_dir = tempfile.mkdtemp(prefix='iris2_')
    logger.debug('Created temp dir "%s"' % temp_dir)
    return temp_dir


_tmp_dir = __create_tempdir()
_run_id = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
_current_module = os.path.join(os.path.expanduser('~'), 'temp', 'test')
args = parse_args()


class PathManager:

    @staticmethod
    def get_current_module():
        """Returns the name of the active test module."""
        return _current_module

    @staticmethod
    def parse_module_path():
        """Returns the parent directory and module name of the calling file."""
        delimiter = '\\' if '\\' in PathManager.get_current_module() else '/'
        temp = PathManager.get_current_module().split(delimiter)
        parent = temp[len(temp) - 2]
        test = temp[len(temp) - 1].split('.py')[0]
        return parent, test

    @staticmethod
    def set_current_module(module):
        """Sets the active module name."""
        global _current_module
        _current_module = module

    @staticmethod
    def get_module_dir():
        """Returns the path to the root of the local Iris repo."""
        return os.path.realpath(os.path.split(__file__)[0] + '/../../..')

    @staticmethod
    def get_tests_dir():
        """Returns the directory where tests are located."""
        return os.path.join(PathManager.get_module_dir(), 'tests')

    @staticmethod
    def get_current_run_dir():
        """Returns the directory inside the working directory of the active run."""
        PathManager.create_run_directory()
        return os.path.join(args.workdir, 'runs', PathManager.get_run_id())

    @staticmethod
    def get_log_file_path():
        """Returns the path to the log file."""
        path = PathManager.get_current_run_dir()
        if not os.path.exists(path):
            os.mkdir(path)
        return os.path.join(path, 'iris_log.log')

    @staticmethod
    def create_test_output_dir():
        """Creates directories inside the current run directory for test output."""
        parent, test = PathManager.parse_module_path()
        parent_directory = os.path.join(PathManager.get_current_run_dir(), parent)
        if not os.path.exists(parent_directory):
            os.makedirs(parent_directory)
        test_directory = os.path.join(parent_directory, test)
        os.mkdir(test_directory)
        return test_directory

    @staticmethod
    def get_tempdir():
        """Returns temporary directory path."""
        return _tmp_dir

    @staticmethod
    def get_run_id():
        """Returns run id based on timestamp."""
        return _run_id

    @staticmethod
    def get_images_path():
        """Returns images directory path."""
        return os.path.join('images', OSHelper.get_os().value)

    @staticmethod
    def delete_run_directory():
        """Removes run directory."""
        master_run_directory = os.path.join(args.workdir, 'runs')
        run_directory = os.path.join(master_run_directory, PathManager.get_run_id())
        if os.path.exists(run_directory):
            shutil.rmtree(run_directory, ignore_errors=True)

    @staticmethod
    def create_working_directory(path):
        """Creates working directory."""
        if not os.path.exists(path):
            logger.debug('Creating working directory %s' % path)
            os.makedirs(path)
        if not os.path.exists(os.path.join(path, 'data')):
            os.makedirs(os.path.join(path, 'data'))

        if args.clear:
            master_run_directory = os.path.join(path, 'runs')
            if os.path.exists(master_run_directory):
                shutil.rmtree(master_run_directory, ignore_errors=True)
            run_file = os.path.join(path, 'data', 'all_runs.json')
            if os.path.exists(run_file):
                os.remove(run_file)
            cache_builds_directory = os.path.join(path, 'cache')
            if os.path.exists(cache_builds_directory):
                shutil.rmtree(cache_builds_directory, ignore_errors=True)

    @staticmethod
    def get_working_dir():
        """Returns the path to the root of the directory where local data is stored."""
        PathManager.create_working_directory(args.workdir)
        return args.workdir

    @staticmethod
    def create_run_directory():
        """Creates run directory."""
        PathManager.create_working_directory(args.workdir)
        master_run_directory = os.path.join(PathManager.get_working_dir(), 'runs')
        if not os.path.exists(master_run_directory):
            os.mkdir(master_run_directory)
        run_directory = os.path.join(master_run_directory, PathManager.get_run_id())
        if not os.path.exists(run_directory):
            os.mkdir(run_directory)

    @staticmethod
    def get_run_directory():
        """Returns the path to the run directory."""
        PathManager.create_run_directory()
        return os.path.join(PathManager.get_working_dir(), 'runs')

    @staticmethod
    def create_target_directory():
        """Creates target directory."""
        PathManager.get_current_run_dir()
        target_directory = os.path.join(PathManager.get_current_run_dir(), args.application)
        if not os.path.exists(target_directory):
            logger.debug('Creating target directory %s' % target_directory)
            os.makedirs(target_directory)

    @staticmethod
    def get_target_directory():
        """Returns the path to the target directory."""
        PathManager.create_target_directory()
        return os.path.join(PathManager.get_current_run_dir(), args.application)

    @staticmethod
    def get_debug_image_directory():
        from pathlib import Path
        test_path = os.environ.get('PYTEST_CURRENT_TEST').split(':')[0]
        return os.path.join(PathManager.get_target_directory(),
                            os.path.splitext(os.path.join(*Path(test_path).parts[2:]))[0], 'debug_images')

    @staticmethod
    def get_git_details():
        repo_details = {}
        repo = git.Repo()
        repo_details['iris_version'] = 0.1
        repo_details['iris_repo'] = repo.working_tree_dir
        repo_details['iris_branch'] = repo.active_branch.name
        repo_details['iris_branch_head'] = repo.head.object.hexsha
        return repo_details