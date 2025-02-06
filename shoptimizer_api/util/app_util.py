# coding=utf-8
# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility that initializes Flask and the global configuration context."""
import json
import logging
import os
import subprocess
from typing import Any, Optional

import flask
import MeCab


def create_app() -> flask.Flask:
  """Initialize the Flask application."""
  app = flask.Flask(__name__)
  app.config['JSON_SORT_KEYS'] = False
  app.config['CONFIGS'] = _load_all_configs()
  app.config['MECAB'] = _setup_mecab()
  app.json.sort_keys = False
  return app


def setup_test_app() -> None:
  """Utility method for unit test setup to access the app context."""
  create_app().app_context().push()


def _load_all_configs() -> dict[str, Any]:
  """Loads into memory the .json config files."""
  all_configs = {}
  config_files_path = os.path.join(os.path.dirname(__file__), '../config/')
  try:
    config_dir = os.fsencode(config_files_path)
    for file in os.listdir(config_dir):
      config_filename = os.fsdecode(file)
      with open(os.path.join(config_files_path,
                             config_filename)) as config_file:
        all_configs[config_filename.split('.')[0]] = json.load(config_file)
  except OSError as os_error:
    logging.exception(
        ('Failed to read the config file. Check that %s exists and has '
         'read permissions. %s'), config_files_path, os_error)
    raise
  except ValueError as value_error:
    logging.exception('Failed to parse the config json. %s', value_error)
    raise
  return all_configs


def _setup_mecab() -> Optional[MeCab.Tagger]:
  """Sets up Mecab tagger for Japanese language non-whitespace token parsing."""
  cmd = 'echo `mecab-config --dicdir`"/mecab-ipadic-neologd"'
  config_path = subprocess.run(
      cmd, stdout=subprocess.PIPE, shell=True,
      check=True).stdout.decode('utf-8')
  try:
    mecab_tagger = MeCab.Tagger(f'-d {config_path}')
    return mecab_tagger
  except RuntimeError as error:
    logging.exception('Error during initializing MeCab Tagger: %s', error)
