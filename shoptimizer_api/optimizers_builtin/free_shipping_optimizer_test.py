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
"""Unit tests for free_shipping_optimizer.py."""

from absl.testing import parameterized

import constants
from optimizers_builtin import free_shipping_optimizer
from test_data import requests_bodies
from util import app_util


class FreeShippingOptimizerTest(parameterized.TestCase):

  def setUp(self):
    super(FreeShippingOptimizerTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = free_shipping_optimizer.FreeShippingOptimizer()

  def test_shipping_field_updated_when_title_has_free_shipping_pattern(self):
    title = 'dummy title free  shipping'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': title},
        properties_to_be_removed=['shipping'])

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']
    shipping = product.get('shipping', [])

    self.assertEqual('0', shipping[0]['price']['value'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_shipping_field_is_not_updated_when_title_does_not_have_free_shipping_pattern(
      self):
    title = 'dummy title'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': title},
        properties_to_be_removed=['shipping'])

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertNotIn('shipping', product)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_shipping_field_is_not_updated_when_title_has_exclusion_pattern(self):
    title = 'dummy title free shipping *exclude islands'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': title},
        properties_to_be_removed=['shipping'])

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertNotIn('shipping', product)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([
      {
          'testcase_name': 'original_value_is_zero',
          'original_value': '0',
      },
      {
          'testcase_name': 'original_value_is_not_zero',
          'original_value': '100',
      },
  ])
  def test_shipping_field_is_not_updated_when_free_shipping_already_exists(
      self, original_value):
    title = 'dummy title free shipping'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                title,
            'shipping': [{
                'price': {
                    'value': original_value,
                    'currency': constants.CURRENCY_CODE_JPY
                },
                'country': constants.COUNTRY_CODE_JP
            }]
        },)

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test', constants.COUNTRY_CODE_JP,
        constants.CURRENCY_CODE_JPY)
    product = optimized_data['entries'][0]['product']
    shipping = product.get('shipping', [])

    self.assertLen(shipping, 1)
    self.assertEqual(0, optimization_result.num_of_products_optimized)
