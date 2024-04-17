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

"""Unit tests for color_length_optimizer.py."""

from absl.testing import parameterized

from optimizers_builtin import color_length_optimizer
from test_data import requests_bodies


class ColorLengthOptimizerTest(parameterized.TestCase):

  def test_color_length_optimizer_does_nothing_when_color_valid_single_value(
      self):
    original_color = 'Blue'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'color': original_color})

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_color, product['color'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_color_length_optimizer_does_nothing_when_color_valid_multiple_values(
      self):
    original_color = 'Blue/White/Red'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'color': original_color})

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_color, product['color'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_color_length_optimizer_does_nothing_when_color_does_not_exist(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_removed=['color'])

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    _, optimization_result = optimizer.process(original_data)

    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_color_length_optimizer_removes_colors_longer_than_forty_chars(self):
    color_with_value_longer_than_forty_chars = 'BlackBlackBlackBlackBlackBlackBlackBlackBlack/Blue'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'color': color_with_value_longer_than_forty_chars
        })

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('Blue', product['color'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_color_length_optimizer_removes_all_when_all_colors_longer_than_forty_chars(
      self):
    color_with_values_longer_than_forty_chars = 'BlackBlackBlackBlackBlackBlackBlackBlackBlack/BlueBlueBlueBlueBlueBlueBlueBlueBlueBlueBlue'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'color': color_with_values_longer_than_forty_chars
        })

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('', product['color'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_color_length_optimizer_removes_all_when_single_color_longer_than_100_chars(
      self):
    color_with_value_more_than_100_chars = (
        'BlackBlackBlackBlackBlackBlackBlackBlackBlackBlack'
        'BlackBlackBlackBlackBlackBlackBlackBlackBlackBlackBlack')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'color': color_with_value_more_than_100_chars
        })

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('', product['color'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_color_optimizer_does_not_remove_color_with_exactly_forty_chars(self):
    color_with_exactly_forty_chars = 'BlackBlackBlackBlackBlackBlackBlackBlack'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'color': color_with_exactly_forty_chars})

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(color_with_exactly_forty_chars, product['color'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_color_length_optimizer_does_nothing_when_length_is_exactly_100(self):
    color_with_three_len_thirty_five_colors = (
        'BlackBlackBlackBlackBlackBlackBla'
        '/WhiteWhiteWhiteWhiteWhiteWhiteWhite'
        '/GreenGreenGreenGreenGreenGreen')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'color': color_with_three_len_thirty_five_colors
        })

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(
        'BlackBlackBlackBlackBlackBlackBla'
        '/WhiteWhiteWhiteWhiteWhiteWhiteWhite'
        '/GreenGreenGreenGreenGreenGreen', product['color'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_color_length_optimizer_removes_colors_until_length_is_less_than_100(
      self):
    color_with_three_len_thirty_five_colors = (
        'BlackBlackBlackBlackBlackBlackBlack'
        '/WhiteWhiteWhiteWhiteWhiteWhiteWhite'
        '/GreenGreenGreenGreenGreenGreenGreen')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'color': color_with_three_len_thirty_five_colors
        })

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(
        'BlackBlackBlackBlackBlackBlackBlack'
        '/WhiteWhiteWhiteWhiteWhiteWhiteWhite', product['color'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_color_length_optimizer_removes_colors_until_only_three_colors_remain(
      self):
    color_with_five_values = 'Blue/White/Red/Black/Orange'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'color': color_with_five_values})

    optimizer = color_length_optimizer.ColorLengthOptimizer()

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('Blue/White/Red', product['color'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)
