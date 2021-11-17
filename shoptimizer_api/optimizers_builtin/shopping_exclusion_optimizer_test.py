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

"""Unit tests for shopping_exclusion_optimizer.py."""

import enums
import unittest.mock as mock

from absl.testing import parameterized

from optimizers_builtin import shopping_exclusion_optimizer
from test_data import requests_bodies
from util import app_util


class ShoppingExclusionOptimizerTest(parameterized.TestCase):

  def setUp(self):
    super(ShoppingExclusionOptimizerTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = shopping_exclusion_optimizer.ShoppingExclusionOptimizer()

  @parameterized.named_parameters([
      {
          'testcase_name':
              'shopping exclusion-detected',
          'test_title':
              '[B2B-only] This should not be on Shopping Ads',
          'included_destinations_attribute': [
              'Some_destination', 'Shopping_ads'
          ],
      },
  ])
  def test_process_sets_shopping_exclusion_attribute_for_non_shopping_products_with_nonexistent_excluded_destinations(
      self, test_title, included_destinations_attribute):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'includedDestinations': included_destinations_attribute
        },
        properties_to_be_removed=['excludedDestinations'])
    optimizer = shopping_exclusion_optimizer.ShoppingExclusionOptimizer()

    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, 'test')

      product = optimized_data['entries'][0]['product']
      self.assertEqual(['Some_destination'],
                       product.get('includedDestinations'))
      self.assertEqual(['Shopping_ads', 'Free_listings'],
                       product.get('excludedDestinations'))
      self.assertEqual(1, optimization_result.num_of_products_optimized)
      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])

  @parameterized.named_parameters([{
      'testcase_name': 'Shopping exclusion-detected with inclusion attribute',
      'test_title': '[B2B-only] This should not be on Shopping Ads',
      'expected_exclusion_attribute': ['Shopping_ads', 'Free_listings'],
      'included_destinations_attribute': [
          'Another_destination', 'Shopping_ads'
      ]
  }, {
      'testcase_name':
          'Shopping exclusion-detected with non-normalized inclusion attribute',
      'test_title':
          '[B2B-only] This should not be on Shopping Ads',
      'expected_exclusion_attribute': ['Shopping_ads', 'Free_listings'],
      'included_destinations_attribute': [
          'Another_destination', 'Shopping ads'
      ]
  }])
  def test_process_sets_shopping_exclusion_attribute_for_non_shopping_products_with_included_destinations(
      self, test_title, expected_exclusion_attribute,
      included_destinations_attribute):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'includedDestinations': included_destinations_attribute,
        })
    optimizer = shopping_exclusion_optimizer.ShoppingExclusionOptimizer()

    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, 'test')

      product = optimized_data['entries'][0]['product']
      self.assertEqual(expected_exclusion_attribute,
                       product.get('excludedDestinations'))
      self.assertEqual(['Another_destination'],
                       product.get('includedDestinations'))
      self.assertEqual(1, optimization_result.num_of_products_optimized)
      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])

  @parameterized.named_parameters([
      {
          'testcase_name':
              'Shopping exclusion-detected with no inclusion attribute',
          'test_title':
              '[B2B-only] This should not be on Shopping Ads',
          'expected_exclusion_attribute': ['Shopping_ads', 'Free_listings'],
      },
  ])
  def test_process_sets_shopping_exclusion_attribute_for_non_shopping_products_with_nonexistent_included_destinations(
      self, test_title, expected_exclusion_attribute):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
        },
        properties_to_be_removed=['includedDestinations'])
    optimizer = shopping_exclusion_optimizer.ShoppingExclusionOptimizer()

    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, 'test')

      product = optimized_data['entries'][0]['product']
      self.assertEqual(expected_exclusion_attribute,
                       product.get('excludedDestinations'))
      self.assertNotIn('includedDestinations', product)
      self.assertEqual(1, optimization_result.num_of_products_optimized)
      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])

  @parameterized.named_parameters([
      {
          'testcase_name': 'Shopping exclusion-undetected',
          'test_title': 'This should be on Shopping Ads',
          'excluded_destinations_attribute': ['Some_excluded_destination'],
          'included_destinations_attribute': ['Shopping_ads']
      },
  ])
  def test_process_doesnt_set_shopping_exclusion_attribute_for_shopping_products_with_included_destinations(
      self, test_title, excluded_destinations_attribute,
      included_destinations_attribute):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'excludedDestinations': excluded_destinations_attribute,
            'includedDestinations': included_destinations_attribute,
        })
    optimizer = shopping_exclusion_optimizer.ShoppingExclusionOptimizer()

    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, 'test')

      product = optimized_data['entries'][0]['product']
      self.assertEqual(
          product.get('excludedDestinations'), excluded_destinations_attribute)
      self.assertEqual(
          product.get('includedDestinations'), included_destinations_attribute)
      self.assertEqual(0, optimization_result.num_of_products_optimized)
      self.assertNotIn('tracking_field', product)

  @parameterized.named_parameters([
      {
          'testcase_name': 'Shopping exclusion-undetected',
          'test_title': 'This should be on Shopping Ads',
          'included_destinations_attribute': ['Shopping_ads']
      },
  ])
  def test_process_doesnt_set_shopping_exclusion_attribute_for_shopping_products_with_nonexistent_excluded_destinations(
      self, test_title, included_destinations_attribute):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'includedDestinations': included_destinations_attribute,
        },
        properties_to_be_removed=['excludedDestinations'])
    optimizer = shopping_exclusion_optimizer.ShoppingExclusionOptimizer()

    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, 'test')

      product = optimized_data['entries'][0]['product']
      self.assertNotIn('excludedDestinations', product)
      self.assertEqual(product.get('includedDestinations'), ['Shopping_ads'])
      self.assertEqual(0, optimization_result.num_of_products_optimized)
      self.assertNotIn('tracking_field', product)

  def test_process_normalizes_shopping_exclusion_attribute_for_non_shopping_products(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': '[B2B-only] This should not be on Shopping Ads',
            'excludedDestinations': ['Shopping ads', 'Free listings'],
        },
        properties_to_be_removed=['includedDestinations'])
    optimizer = shopping_exclusion_optimizer.ShoppingExclusionOptimizer()

    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, 'test')

      product = optimized_data['entries'][0]['product']
      self.assertEqual(['Shopping_ads', 'Free_listings'],
                       product.get('excludedDestinations'))
      self.assertEqual(1, optimization_result.num_of_products_optimized)
      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])
