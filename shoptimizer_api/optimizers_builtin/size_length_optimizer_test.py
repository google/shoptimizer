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
"""Unit tests for size_length_optimizer.py."""
import unittest.mock as mock

from absl.testing import parameterized

import enums
from optimizers_builtin import size_length_optimizer
from test_data import requests_bodies


class SizeLengthOptimizerTest(parameterized.TestCase):

  def test_size_length_optimizer_does_nothing_when_size_valid(self):
    original_size = 'Small'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'sizes': [original_size]})
    optimizer = size_length_optimizer.SizeLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_size, product['sizes'][0])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_size_length_optimizer_truncates_size_when_more_than_max_chars(self):
    size_more_than_100_chars = ('SmallSmallSmallSmallSmallSmallSmallSmall'
                                'SmallSmallSmallSmallSmallSmallSmallSmall'
                                'SmallSmallSmallSmallSmallSmallSmallSmall')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'sizes': [size_more_than_100_chars]})
    optimizer = size_length_optimizer.SizeLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('SmallSmallSmallSmallSmallSmallSmall'
                     'SmallSmallSmallSmallSmallSmallSmall'
                     'SmallSmallSmallSmallSmallSmall', product['sizes'][0])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_size_length_optimizer_does_nothing_when_size_equals_max_chars(self):
    size_with_100_chars = ('SmallSmallSmallSmallSmallSmallSmallSmall'
                           'SmallSmallSmallSmallSmallSmallSmallSmall'
                           'SmallSmallSmallSmall')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'sizes': [size_with_100_chars]})
    optimizer = size_length_optimizer.SizeLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(size_with_100_chars,
                     product['sizes'][0])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_size_length_optimizer_does_nothing_when_sizes_not_in_product(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_removed=['sizes'])
    optimizer = size_length_optimizer.SizeLengthOptimizer()

    _, optimization_result = optimizer.process(original_data)

    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_size_length_optimizer_does_nothing_when_sizes_has_no_values(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'sizes': []})
    optimizer = size_length_optimizer.SizeLengthOptimizer()

    _, optimization_result = optimizer.process(original_data)

    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_size_length_optimizer_sets_product_tracking_field_to_sanitized_when_invalid_size_trimmed(
      self):
    size_more_than_100_chars = ('SmallSmallSmallSmallSmallSmallSmallSmall'
                                'SmallSmallSmallSmallSmallSmallSmallSmall'
                                'SmallSmallSmallSmallSmallSmallSmallSmall')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'sizes': [size_more_than_100_chars]})
    optimizer = size_length_optimizer.SizeLengthOptimizer()
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = optimizer.process(original_data)
      product = optimized_data['entries'][0]['product']

      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])

  def test_size_length_optimizer_trims_sizes_when_more_than_one_size_provided(
      self):
    size_more_than_one_value = ['Small', 'Medium', 'Large']
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'sizes': size_more_than_one_value})
    optimizer = size_length_optimizer.SizeLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('Small', product['sizes'][0])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_size_length_optimizer_does_nothing_when_size_empty(self):
    size_with_empty_value = []
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'sizes': size_with_empty_value})
    optimizer = size_length_optimizer.SizeLengthOptimizer()

    _, optimization_result = optimizer.process(original_data)

    self.assertEqual(0, optimization_result.num_of_products_optimized)
