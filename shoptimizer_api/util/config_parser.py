# coding=utf-8
# Copyright 2024 Google LLC.
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

"""Helper module for parsing configuration file overrides."""

import ast
import base64
import logging
from typing import Any, Dict

from flask import current_app


def get_config_contents(config_override_key: str,
                        config_filename: str) -> Dict[str, Any]:
  """Translates either an overridden config or local file into a dictionary.

  Args:
    config_override_key: The config override key to lookup in the Flask headers.
    config_filename: The local (container) filename of the config if not
      overridden.

  Returns:
    A Dictionary representation of the config file contents.
  """
  config_override = current_app.config.get(
      'DRIVE_CONFIG_OVERRIDES', {}).get(config_override_key, '')
  if config_override:
    config = ast.literal_eval(
        base64.b64decode(config_override).decode('UTF-8').strip('\n').strip(
            ' '))
    logging.info('OVERRIDDEN CONFIG CONTENTS: %s', str(config))
  else:
    config = current_app.config.get('CONFIGS', {}).get(config_filename, {})
  return config

