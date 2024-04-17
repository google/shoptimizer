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

"""Unit tests for title_length_optimizer.py."""

from absl.testing import parameterized
import unittest.mock as mock

import enums
from optimizers_builtin import title_length_optimizer
from test_data import requests_bodies


class TitleLengthOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(TitleLengthOptimizerTest, self).setUp()
    self.optimizer = title_length_optimizer.TitleLengthOptimizer()

  def test_process_truncates_title_when_it_is_too_long(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'a' * (title_length_optimizer._MAX_TITLE_LENGTH * 2)
        })

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    expected_title = 'a' * title_length_optimizer._MAX_TITLE_LENGTH
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_not_truncate_title_when_title_length_equal_to_the_max(
      self):
    original_title = 'a' * title_length_optimizer._MAX_TITLE_LENGTH
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': original_title})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters({
      'testcase_name': 'empty',
      'suffix': ''
  }, {
      'testcase_name': 'one period',
      'suffix': '.'
  }, {
      'testcase_name': 'two periods',
      'suffix': '..'
  }, {
      'testcase_name': 'three periods',
      'suffix': '...'
  }, {
      'testcase_name': 'one ellipsis',
      'suffix': '…'
  }, {
      'testcase_name': 'two ellipses',
      'suffix': '……'
  })
  def test_process_puts_the_first_part_of_description_into_title_when_title_is_truncated_from_description(
      self, suffix):
    original_description = 'a' * (title_length_optimizer._MAX_TITLE_LENGTH * 2)
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'a' * (title_length_optimizer._MAX_TITLE_LENGTH - 5) + suffix,
            'description':
                original_description
        })

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    expected_title = (
        original_description[:title_length_optimizer._MAX_TITLE_LENGTH])
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_does_not_change_data_when_title_is_not_truncated_from_description(
      self):
    original_title = 'b'
    original_description = 'a' * (title_length_optimizer._MAX_TITLE_LENGTH * 2)
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'description': original_description
        })

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_sets_product_tracking_field_to_sanitized_when_title_truncated(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'a' * (title_length_optimizer._MAX_TITLE_LENGTH * 2)
        })
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = self.optimizer.process(
          original_data)
      product = optimized_data['entries'][0]['product']

      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])

  def test_process_sets_product_tracking_field_to_optimized_when_title_untruncated(
      self):
    original_description = 'a' * (title_length_optimizer._MAX_TITLE_LENGTH * 2)
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'a' * (title_length_optimizer._MAX_TITLE_LENGTH - 5) + '...',
            'description':
                original_description
        })
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = self.optimizer.process(
          original_data)
      product = optimized_data['entries'][0]['product']

      self.assertEqual(enums.TrackingTag.OPTIMIZED.value,
                       product[tracking_field])

  def test_process_does_not_set_product_tracking_field_when_title_equals_description(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Beauty product',
            'description': 'Beauty product'
        })
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = self.optimizer.process(original_data)
      optimized_product = optimized_data['entries'][0]['product']

      self.assertEqual('', optimized_product[tracking_field])
      self.assertEqual(original_data, optimized_data)

  def test_process_does_not_set_product_tracking_field_when_title_equals_description_but_has_ellipsis_removed(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Beauty product...test',
            'description': 'Beauty product...test'
        })
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = self.optimizer.process(original_data)
      optimized_product = optimized_data['entries'][0]['product']

      self.assertEqual('', optimized_product[tracking_field])
      self.assertEqual(original_data, optimized_data)
