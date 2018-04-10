# Databricks CLI
# Copyright 2017 Databricks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"), except
# that the use of services to which certain application programming
# interfaces (each, an "API") connect requires that the user first obtain
# a license for the use of the APIs from Databricks, Inc. ("Databricks"),
# by creating an account at www.databricks.com and agreeing to either (a)
# the Community Edition Terms of Service, (b) the Databricks Terms of
# Service, or (c) another written agreement between Licensee and Databricks
# for the use of the APIs.
#
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
from git import Repo
import os

from databricks_cli.utils import eat_exceptions, error_and_quit, CONTEXT_SETTINGS
from databricks_cli.version import print_version_callback, version
from databricks_cli.configure.cli import configure_cli
from databricks_cli.configure.config import provide_api_client, profile_option
from databricks_cli.workspace.api import WorkspaceApi
from databricks_cli.workspace.cli import _import_dir_helper, _export_dir_helper, WorkspaceLanguage

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('path')
@profile_option
@provide_api_client
def push_cli(api_client, path=None):
    """
    Push files to workspace.
    """
    repo = Repo.init('.')
    reader = repo.config_reader()
    workspace_dir = reader.get_value('databricks "workspace"', 'path')
    repo.close()
    
    if workspace_dir is None:
        error_and_quit('Git configuration is missing `databricks.workspace.path` value')
    
    if path is None:
        path = '.'
    elif os.path.isabs(path):
        error_and_quit('Path needs to be relative to repo')
    elif not os.path.exists(path):
        error_and_quit('Path not found')
    
    if os.path.isfile(path):
        ext = WorkspaceLanguage.get_extension(path)
        if ext != '':
            cur_dst = workspace_dir.rstrip('/') + '/' + path[:-len(ext)]
            (language, file_format) = WorkspaceLanguage.to_language_and_format(path)
            WorkspaceApi(api_client).import_workspace(path, cur_dst, language, file_format, True)
            click.echo('{} -> {}'.format(path, cur_dst))
        else:
            extensions = ', '.join(WorkspaceLanguage.EXTENSIONS)
            error_and_quit(('{} does not have a valid extension of {}.').format(path, extensions))        
    elif os.path.isdir(path):
        workspace_dir = workspace_dir.rstrip('/') + '/' + path
        _import_dir_helper(WorkspaceApi(api_client), path, workspace_dir, True, True)

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('path')
@click.option('--force', '-f', is_flag=True, default=False)
@profile_option
@eat_exceptions
@provide_api_client
def pull_cli(api_client, path=None, force=False):
    """
    Pull files from workspace.
    """
    repo = Repo.init('.')
    reader = repo.config_reader()
    workspace_dir = reader.get_value('databricks "workspace"', 'path')

    if workspace_dir is None:
        error_and_quit('Git configuration is missing `databricks.workspace.path` value')

    if not force and repo.is_dirty:
        error_and_quit('Repository has uncomitted files, to overwrite, use `--force`')

    _export_dir_helper(WorkspaceApi(api_client), workspace_dir, '.', True)

@click.group(context_settings=CONTEXT_SETTINGS, short_help='Utility to interact with Git.')
@click.option('--version', '-v', is_flag=True, callback=print_version_callback,
              expose_value=False, is_eager=True, help=version)
@profile_option
def git_group():
    """
    Utility to interact with Git.
    """
    pass

git_group.add_command(push_cli, name='push')
git_group.add_command(pull_cli, name='pull')
