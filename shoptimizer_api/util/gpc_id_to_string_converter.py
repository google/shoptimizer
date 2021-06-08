# coding=utf-8
# Copyright 2021 Google LLC.
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

"""Utility module that converts GPCs as ID numbers into their mapped strings."""


from typing import Union
from flask import current_app

_GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME: str = 'gpc_string_to_id_mapping_{}'


class GPCConverter(object):
  """A class that handles conversion from GPC ID to String."""

  def __init__(self, gpc_string_to_id_mapping_file_name: str) -> None:
    """Initializes GPCConverter.

    Args:
      gpc_string_to_id_mapping_file_name: The name of the config file.
    """
    self._gpc_string_to_id_mapping = (
        current_app.config.get('CONFIGS',
                               {}).get(gpc_string_to_id_mapping_file_name, {}))

  def convert_gpc_id_to_string(self, gpc: Union[str, int]) -> str:
    """Looks up and returns the string format of the GPC if it is a number."""
    if isinstance(gpc, int) or gpc.isdigit():
      gpc_string = ''
      for key, value in self._gpc_string_to_id_mapping.items():
        if value == int(gpc):
          gpc_string = key
          break
      return gpc_string or ''
    else:
      return gpc
