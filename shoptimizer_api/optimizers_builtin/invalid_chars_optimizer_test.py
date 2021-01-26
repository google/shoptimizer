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
"""Unit tests for invalid_chars_optimizer.py."""
import unittest.mock as mock

from absl.testing import parameterized

import enums
from optimizers_builtin import invalid_chars_optimizer
from test_data import requests_bodies


class InvalidCharsOptimizerTest(parameterized.TestCase):

  def test_invalid_chars_optimizer_removes_single_invalid_char(self):
    # Char in pos 10 is invalid
    title_with_single_invalid_char = 'Brand １５０ｇ Product Title'
    desc_with_single_invalid_char = 'Brand １５０ｇ Product Desc'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': title_with_single_invalid_char,
            'description': desc_with_single_invalid_char
        })
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('Brand １５０ｇ Product Title', product['title'])
    self.assertEqual('Brand １５０ｇ Product Desc', product['description'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_removes_multiple_invalid_chars(self):
    # Chars in pos 10 & pos 11 are invalid
    title_with_multiple_invalid_chars = 'Brand １５０ｇ Product Title'
    desc_with_multiple_invalid_chars = 'Brand １５０ｇ Product Desc'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': title_with_multiple_invalid_chars,
            'description': desc_with_multiple_invalid_chars
        })
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('Brand １５０ｇ Product Title', product['title'])
    self.assertEqual('Brand １５０ｇ Product Desc', product['description'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_removes_first_char_in_unicode_private_area(
      self):
    title_with_first_char_in_unicode_private_area = (f'Brand １５０ｇ{chr(0xE000)} '
                                                     f'Product Desc')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': title_with_first_char_in_unicode_private_area
        })
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('Brand １５０ｇ Product Desc', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_removes_last_char_in_unicode_private_area(
      self):
    title_with_last_char_in_unicode_private_area = (f'Brand １５０ｇ{chr(0xF8FF)} '
                                                    f'Product Desc')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': title_with_last_char_in_unicode_private_area
        })
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('Brand １５０ｇ Product Desc', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_does_not_remove_last_char_before_unicode_private_area(
      self):
    title_with_last_char_before_unicode_private_area = (f'Brand '
                                                        f'１５０ｇ{chr(0xDFFF)} '
                                                        f'Product Desc')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': title_with_last_char_before_unicode_private_area
        })
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(title_with_last_char_before_unicode_private_area,
                     product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_does_not_remove_first_char_after_unicode_private_area(
      self):
    title_with_first_char_after_unicode_private_area = (f'Brand '
                                                        f'１５０ｇ{chr(0xF900)} '
                                                        f'Product Desc')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': title_with_first_char_after_unicode_private_area
        })
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(title_with_first_char_after_unicode_private_area,
                     product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_does_nothing_when_all_chars_valid(self):
    title_with_no_invalid_chars = 'Brand １５０ｇ Product Desc'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': title_with_no_invalid_chars})
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(title_with_no_invalid_chars, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_does_nothing_when_title_and_description_do_not_exist(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_removed=['title', 'description'])
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    _, optimization_result = optimizer.process(original_data)

    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_does_nothing_when_title_and_description_empty(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': '', 'description': ''})
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()

    _, optimization_result = optimizer.process(original_data)

    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_invalid_chars_optimizer_sets_product_tracking_field_to_sanitized_when_invalid_char_removed(
      self):
    # Char in pos 10 is invalid
    title_with_single_invalid_char = 'Brand １５０ｇ Product Desc'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': title_with_single_invalid_char})
    optimizer = invalid_chars_optimizer.InvalidCharsOptimizer()
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = optimizer.process(original_data)
      product = optimized_data['entries'][0]['product']

      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])
