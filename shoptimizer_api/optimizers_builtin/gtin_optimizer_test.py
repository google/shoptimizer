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

# python3
"""Unit tests for gtin_optimizer.py."""

from absl.testing import parameterized

from optimizers_builtin import gtin_optimizer
from test_data import requests_bodies


class GTINOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(GTINOptimizerTest, self).setUp()
    self.optimizer = gtin_optimizer.GTINOptimizer()

  @parameterized.named_parameters([{
      'testcase_name': 'empty',
      'test_gtin': ''
  }, {
      'testcase_name': 'invalid 7-digit GTIN',
      'test_gtin': '9504000'
  }, {
      'testcase_name': 'invalid 15-digit GTIN',
      'test_gtin': '009781594741753'
  }, {
      'testcase_name': 'invalid 8-digit GTIN',
      'test_gtin': '12345678'
  }, {
      'testcase_name': 'invalid 12-digit GTIN',
      'test_gtin': '978159474175'
  }, {
      'testcase_name': 'invalid 13-digit GTIN',
      'test_gtin': '9781594741754'
  }, {
      'testcase_name': 'invalid 14-digit GTIN',
      'test_gtin': '12345678901234'
  }, {
      'testcase_name': 'invalid GTIN with letters',
      'test_gtin': '123456789z1234'
  }, {
      'testcase_name': 'invalid repeating-number GTIN',
      'test_gtin': '1111111111116'
  }, {
      'testcase_name': 'invalid sequential-number GTIN',
      'test_gtin': '123456789999'
  }])
  def test_gtin_optimizer_removes_gtin_from_request_on_invalid_gtins(
      self, test_gtin):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'gtin': test_gtin})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertNotIn('gtin', product)
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'valid 13-digit GTIN',
      'test_gtin': '9504000059422'
  }, {
      'testcase_name': 'another valid 13-digit GTIN',
      'test_gtin': '9781594741753'
  }])
  def test_gtin_optimizer_does_not_transform_valid_data(self, test_gtin):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'gtin': test_gtin})

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_gtin_optimizer_does_not_transform_data_when_gtin_field_missing(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_removed=['gtin'])

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
    self.assertEqual(0, optimization_result.num_of_products_optimized)
