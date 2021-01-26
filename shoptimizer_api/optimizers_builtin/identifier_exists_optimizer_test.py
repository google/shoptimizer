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
"""Unit tests for identifier_exists_optimizer.py."""

import unittest.mock as mock

from absl.testing import parameterized

import enums
from optimizers_builtin import identifier_exists_optimizer
from test_data import requests_bodies


class IdentifierExistsOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(IdentifierExistsOptimizerTest, self).setUp()
    self.optimizer = identifier_exists_optimizer.IdentifierExistsOptimizer()

  def test_process_removes_false_identifier_exists_field_when_brand_set(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'identifierExists': False,
            'brand': 'testbrand',
            'mpn': '',
            'gtin': '',
        })

    optimized_data, optimization_result = self.optimizer.process(original_data)
    api_response_result = optimized_data['entries'][0]['product']

    self.assertNotIn('identifierExists', api_response_result)
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_removes_false_identifier_exists_field_when_gtin_set(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'identifierExists': False,
            'brand': '',
            'mpn': '',
            'gtin': '12345',
        })

    optimized_data, optimization_result = self.optimizer.process(original_data)
    api_response_result = optimized_data['entries'][0]['product']

    self.assertNotIn('identifierExists', api_response_result)
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_removes_false_identifier_exists_field_when_mpn_set(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'identifierExists': False,
            'brand': '',
            'mpn': '12345',
            'gtin': '',
        })

    optimized_data, optimization_result = self.optimizer.process(original_data)
    api_response_result = optimized_data['entries'][0]['product']

    self.assertNotIn('identifierExists', api_response_result)
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_does_not_transform_valid_data(self):
    original_data = requests_bodies.build_request_body()

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_transform_data_when_identifier_exists_field_missing(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_removed=['identifierExists'])

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_sets_product_tracking_field_to_sanitized_when_invalid_identifier_exists_removed(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'identifierExists': False,
            'brand': 'testbrand',
            'mpn': '',
            'gtin': '',
        })
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = self.optimizer.process(
          original_data)
      optimized_product = optimized_data['entries'][0]['product']

      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       optimized_product[tracking_field])
