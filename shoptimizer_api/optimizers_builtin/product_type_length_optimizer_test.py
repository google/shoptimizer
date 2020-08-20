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
"""Unit tests for product_type_length_optimizer module."""

from typing import List
import unittest.mock as mock

from absl.testing import parameterized

import enums
from optimizers_builtin import product_type_length_optimizer
from test_data import requests_bodies


class ProductTypeLengthOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(ProductTypeLengthOptimizerTest, self).setUp()
    self.optimizer = product_type_length_optimizer.ProductTypeLengthOptimizer()

  def test_process_cut_product_type_when_it_has_too_many_items(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'productTypes': ['a'] *
                            (product_type_length_optimizer._MAX_LIST_LENGTH + 1)
        })

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    expected_product_type = ['a'
                            ] * product_type_length_optimizer._MAX_LIST_LENGTH
    self.assertEqual(expected_product_type, product['productTypes'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters(
      {
          'testcase_name': 'empty',
          'original_product_type': []
      },
      {
          'testcase_name': 'one item',
          'original_product_type': ['a']
      },
      {
          'testcase_name':
              'equal to max list length',
          'original_product_type':
              ['a'] * product_type_length_optimizer._MAX_LIST_LENGTH
      },
  )
  def test_process_not_cut_product_type_when_not_too(
      self, original_product_type: List[str]):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'productTypes': original_product_type})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_product_type, product['productTypes'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_succeed_when_product_type_not_exist(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_removed=['productTypes'])

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
    self.assertEqual('success', optimization_result.result)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_sets_product_tracking_field_to_sanitized_when_product_type_truncated(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'productTypes': ['a'] *
                            (product_type_length_optimizer._MAX_LIST_LENGTH + 1)
        })
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = self.optimizer.process(original_data)
      product = optimized_data['entries'][0]['product']

      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])
