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

"""Tests for Config Parser."""

from unittest import mock

from absl.testing import parameterized
from util import app_util
from util import config_parser


# Test case uses the base64 representation of this config:
# {
#  "color_terms" : {
#    "イエロー": "イエロー",
#    "オレンジ": "オレンジ",
#    "アプリコット": "オレンジ",
#  }
# }
_BASE_64_CONFIG = 'ewogICJjb2xvcl90ZXJtcyIgOiB7CiAgICAi44Kk44Ko44Ot44O8IjogIuOCpOOCqOODreODvCIsCiAgICAi44Kq44Os44Oz44K4IjogIuOCquODrOODs+OCuCIsCiAgICAi44Ki44OX44Oq44Kz44OD44OIIjogIuOCquODrOODs+OCuCIsCiAgfQp9'


@mock.patch.dict(
    'flask.current_app.config', {
        'DRIVE_CONFIG_OVERRIDES': {
            'color_optimizer_config_override': _BASE_64_CONFIG
        }
    })
class ConfigParserTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    app_util.setup_test_app()

  @parameterized.named_parameters([{
      'testcase_name': 'override',
      'config_override_key': 'color_optimizer_config_override',
      'config_filename': 'color_optimizer_config_test',
  }])
  def test_get_config_contents_creates_dict_from_valid_override(
      self, config_override_key, config_filename):
    config = config_parser.get_config_contents(config_override_key,
                                               config_filename)
    self.assertEqual(config['color_terms']['アプリコット'], 'オレンジ')

  @parameterized.named_parameters([{
      'testcase_name': 'filename',
      'config_override_key': 'unknown',
      'config_filename': 'color_optimizer_config_test',
  }])
  def test_get_config_contents_creates_dict_from_valid_file(
      self, config_override_key, config_filename):
    config = config_parser.get_config_contents(config_override_key,
                                               config_filename)
    self.assertEqual(config['color_terms']['apricot'], 'orange')

  @parameterized.named_parameters([{
      'testcase_name': 'filename',
      'config_override_key': 'unknown',
      'config_filename': 'unknown',
  }])
  def test_get_config_contents_returns_empty_dict_when_no_config_matches(
      self, config_override_key, config_filename):
    config = config_parser.get_config_contents(config_override_key,
                                               config_filename)
    self.assertEqual(config, {})
