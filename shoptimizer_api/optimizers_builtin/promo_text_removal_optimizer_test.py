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

"""Unit tests for promo_text_removal_optimizer.py."""

from absl.testing import parameterized
import unittest.mock as mock

import constants
import enums
from optimizers_builtin import promo_text_removal_optimizer
from test_data import requests_bodies
from util import app_util


@mock.patch('util.promo_text_remover._PROMO_TEXT_REMOVAL_CONFIG_FILE_NAME',
            'promo_text_removal_optimizer_config_{}_test')
class PromoTextRemovalOptimizerTest(parameterized.TestCase):

  def setUp(self):
    super(PromoTextRemovalOptimizerTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = promo_text_removal_optimizer.PromoTextRemovalOptimizer()
    self.fields_to_append = ['gender', 'color', 'sizes', 'brand']

  @parameterized.named_parameters([
      {
          'testcase_name': '送料無料',
          'original_title': '送料無料Tシャツ',
          'expected_title': 'Tシャツ'
      },
      {
          'testcase_name': '送料込',
          'original_title': '送料込 Tシャツ',
          'expected_title': 'Tシャツ'
      },
      {
          'testcase_name': '一部地域除く',
          'original_title': '送料無料一部地域除く Tシャツ',
          'expected_title': 'Tシャツ'
      },
  ])
  def test_process_removes_japanese_promotional_text_by_exact_match(
      self, original_title, expected_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
        },
        properties_to_be_removed=self.fields_to_append)
    optimizer = promo_text_removal_optimizer.PromoTextRemovalOptimizer()

    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, constants.LANGUAGE_CODE_JA)

      product = optimized_data['entries'][0]['product']
      self.assertEqual(expected_title, product['title'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)
      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])

  @parameterized.named_parameters([{
      'testcase_name': '【 送料無料 】',
      'original_title': '【 送料無料 】Tシャツ',
      'expected_title': 'Tシャツ'
  }, {
      'testcase_name': '一部地域を除く',
      'original_title': 'Tシャツ 一部地域を除く',
      'expected_title': 'Tシャツ'
  }])
  def test_process_removes_japanese_promotional_text_by_regex(
      self, original_title, expected_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
        },
        properties_to_be_removed=self.fields_to_append)
    optimizer = promo_text_removal_optimizer.PromoTextRemovalOptimizer()

    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, constants.LANGUAGE_CODE_JA)

      product = optimized_data['entries'][0]['product']
      self.assertEqual(expected_title, product['title'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)
      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])

  @parameterized.named_parameters([{
      'testcase_name': 'regex_ahead',
      'original_title': '【 送料無料 】Tシャツ お得な送料無料',
      'expected_title': 'Tシャツ'
  }, {
      'testcase_name':
          'exact_match_ahead',
      'original_title':
          'Tシャツ メール便のみ送料無料 (一部地域除く)',
      'expected_title':
          'Tシャツ'
  }])
  def test_process_removes_japanese_promotional_text_by_both_exact_match_and_regex(
      self, original_title, expected_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
        },
        properties_to_be_removed=self.fields_to_append)
    optimizer = promo_text_removal_optimizer.PromoTextRemovalOptimizer()
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, optimization_result = optimizer.process(
          original_data, constants.LANGUAGE_CODE_JA)

      product = optimized_data['entries'][0]['product']
      self.assertEqual(expected_title, product['title'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)
      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       product[tracking_field])
