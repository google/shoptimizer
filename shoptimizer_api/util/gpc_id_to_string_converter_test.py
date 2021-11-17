# coding=utf-8
# Copyright 2022 Google LLC.
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

"""Unit tests for gpc_id_to_string_converter.py."""

import unittest

import constants
from util import app_util
from util import gpc_id_to_string_converter

_GPC_STRING_TO_ID_MAPPING_CONFIG_TEST_FILE_NAME = 'gpc_string_to_id_mapping_{}_test'

_GPC_STRING_TO_ID_MAPPING_CONFIG_TEST_DICT = {
    'Animals & Pet Supplies > Pet Supplies > Cat Supplies > Cat Food': 3367,
}


class GPCIDToStringConverterTest(unittest.TestCase):

  def setUp(self):
    super(GPCIDToStringConverterTest, self).setUp()
    app_util.setup_test_app()

  def test_gpc_id_to_string_converter_correctly_converts_gpc_id_to_string(self):
    test_gpc_converter = gpc_id_to_string_converter.GPCConverter(
        _GPC_STRING_TO_ID_MAPPING_CONFIG_TEST_FILE_NAME.format(
            constants.LANGUAGE_CODE_EN))
    gpc_string = test_gpc_converter.convert_gpc_id_to_string(3367)
    self.assertEqual(
        'Animals & Pet Supplies > Pet Supplies > Cat Supplies > Cat Food',
        gpc_string)

  def test_gpc_id_to_string_converter_correctly_converts_using_dict_constructor(
      self):
    test_gpc_converter = (
        gpc_id_to_string_converter.GPCConverter.from_dictionary(
            _GPC_STRING_TO_ID_MAPPING_CONFIG_TEST_DICT))
    gpc_string = test_gpc_converter.convert_gpc_id_to_string(3367)
    self.assertEqual(
        'Animals & Pet Supplies > Pet Supplies > Cat Supplies > Cat Food',
        gpc_string)

  def test_gpc_id_to_string_converter_returns_empty_string_for_invalid_id(self):
    test_gpc_converter = gpc_id_to_string_converter.GPCConverter(
        _GPC_STRING_TO_ID_MAPPING_CONFIG_TEST_FILE_NAME.format(
            constants.LANGUAGE_CODE_EN))
    gpc_string = test_gpc_converter.convert_gpc_id_to_string(99999)
    self.assertEqual('', gpc_string)

  def test_gpc_id_to_string_converter_returns_same_string_for_gpc_string(self):
    original_gpc_string = ('Animals & Pet Supplies > Pet Supplies > Cat '
                           'Supplies > Cat Food')
    test_gpc_converter = gpc_id_to_string_converter.GPCConverter(
        _GPC_STRING_TO_ID_MAPPING_CONFIG_TEST_FILE_NAME.format(
            constants.LANGUAGE_CODE_EN))
    gpc_string = test_gpc_converter.convert_gpc_id_to_string(
        original_gpc_string)
    self.assertEqual(original_gpc_string, gpc_string)
