# coding=utf-8
# Copyright 2020 Google LLC.
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

# python3
"""Unit tests for requests_bodies.py."""

import json

from absl.testing import parameterized

from test_data import requests_bodies


class RequestsBodiesTests(parameterized.TestCase):
  """Class to test requests_bodies.py against expected json files."""

  @parameterized.named_parameters([
      {
          'testcase_name': 'no_transformations',
          'properties_to_be_updated': None,
          'properties_to_be_removed': None,
          'expected_json_file': 'test_product_identity.json',
      },
      {
          'testcase_name': 'deletes',
          'properties_to_be_updated': None,
          'properties_to_be_removed': {'gtin', 'mpn'},
          'expected_json_file': 'test_product_deletes.json',
      },
      {
          'testcase_name': 'updates',
          'properties_to_be_updated': {
              'mpn': '12345'
          },
          'properties_to_be_removed': None,
          'expected_json_file': 'test_product_updates.json',
      },
      {
          'testcase_name': 'updates_deletes',
          'properties_to_be_updated': {
              'gtin': '1'
          },
          'properties_to_be_removed': {'mpn'},
          'expected_json_file': 'test_product_updates_deletes.json',
      },
  ])
  def test_build_request_body(self, properties_to_be_updated,
                              properties_to_be_removed, expected_json_file):
    """Tests build_request_body."""
    with open(expected_json_file, 'r') as test_product:
      expected_result = json.load(test_product)

    actual_result = requests_bodies.build_request_body(
        properties_to_be_updated, properties_to_be_removed)
    self.assertEqual(expected_result, actual_result)
