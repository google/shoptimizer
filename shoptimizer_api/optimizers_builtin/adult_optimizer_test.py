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

"""Unit tests for adult_optimizer.py."""

from absl.testing import parameterized
from unittest import mock

from optimizers_builtin import adult_optimizer
from test_data import requests_bodies
from util import app_util


@mock.patch(
    'optimizers_builtin.adult_optimizer._GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME',
    'gpc_string_to_id_mapping_{}_test')
class AdultOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(AdultOptimizerTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = adult_optimizer.AdultOptimizer()

  @parameterized.named_parameters([{
      'testcase_name': 'Idol Category',
      'is_adult': False,
      'test_product_types': ['CD・DVD, Blu-ray', 'アイドル', 'その他'],
  }, {
      'testcase_name':
          'Alcohol Category',
      'is_adult':
          False,
      'test_product_types': [
          'ビール・洋酒', 'リキュール',
          'ハーブ・スパイス・ティー系', 'その他'
      ],
  }])
  def test_adult_optimizer_sets_adult_to_true_if_product_type_is_adult(
      self, is_adult, test_product_types):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'adult': is_adult,
            'productTypes': test_product_types
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(True, product['adult'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'Adult Not Set',
      'test_product_types': ['CD・DVD, Blu-ray', 'アイドル', 'その他'],
  }])
  def test_adult_optimizer_sets_adult_to_true_if_product_type_is_adult_and_adult_not_set(
      self, test_product_types):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'productTypes': test_product_types})

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(True, product['adult'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'Adult GPC',
      'test_google_product_category': '成人向け',
      'test_title': 'No suspicious tokens',
  }, {
      'testcase_name':
          'Another Adult GPC',
      'test_google_product_category':
          '成人向け > アダルト > アダルト雑誌',
      'test_title':
          'No suspicious tokens',
  }])
  def test_adult_optimizer_sets_adult_to_true_if_gpc_is_adult_and_tokens_are_wildcard(
      self, test_google_product_category, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'googleProductCategory': test_google_product_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(True, product['adult'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'Adult GPC as ID',
      'test_google_product_category': 772,
      'test_title': 'No suspicious tokens',
  }, {
      'testcase_name': 'Another Adult GPC as ID',
      'test_google_product_category': 4060,
      'test_title': 'No suspicious tokens',
  }])
  def test_adult_optimizer_sets_adult_to_true_if_gpc_is_adult_as_an_id_number(
      self, test_google_product_category, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'googleProductCategory': test_google_product_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'ja')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(True, product.get('adult', ''))
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'Idol in Title',
      'test_google_product_category': 'メディア > DVD・ビデオ',
      'test_title': 'アイドル DVD',
  }, {
      'testcase_name': 'Gravure in Title',
      'test_google_product_category': 'メディア > DVD・ビデオ',
      'test_title': 'DVD グラビア',
  }])
  def test_adult_optimizer_sets_adult_to_true_if_gpc_and_title_is_adult(
      self, test_google_product_category, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'googleProductCategory': test_google_product_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(True, product['adult'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'Idol in Description',
      'test_description': 'アイドル DVD',
      'test_google_product_category': 'メディア > DVD・ビデオ',
  }, {
      'testcase_name': 'Gravure in Description',
      'test_description': 'DVD グラビア',
      'test_google_product_category': 'メディア > DVD・ビデオ',
  }])
  def test_adult_optimizer_sets_adult_to_true_if_gpc_and_description_is_adult(
      self, test_google_product_category, test_description):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': test_description,
            'googleProductCategory': test_google_product_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(True, product['adult'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name':
          'Game Category',
      'is_adult':
          False,
      'test_product_types': [
          'テレビゲーム', 'プレイステーション4', '周辺機器'
      ],
  }])
  def test_adult_optimizer_does_nothing_if_category_is_not_adult(
      self, is_adult, test_product_types):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'adult': is_adult,
            'productTypes': test_product_types
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(False, product['adult'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'DVD Category',
      'is_adult': False,
      'test_google_product_category': 'メディア > DVD・ビデオ',
      'test_title': '何も怪しいことない',
  }, {
      'testcase_name': 'Books Category',
      'is_adult': False,
      'test_google_product_category': 'メディア > 書籍',
      'test_title': '何も怪しいことない',
  }])
  def test_adult_optimizer_does_nothing_if_category_is_adult_but_no_adult_tokens_in_title(
      self, is_adult, test_google_product_category, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'adult': is_adult,
            'googleProductCategory': test_google_product_category,
            'title': test_title
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(False, product['adult'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'Home Garden Category',
      'is_adult': False,
      'test_google_product_category':
          'ホーム・ガーデン > キッチン・ダイニング > '
          '調理器具',
      'test_title': 'グラビア 器具',
  }, {
      'testcase_name': 'DIY Category',
      'is_adult': False,
      'test_google_product_category': 'DIY用品 > DIY小物類',
      'test_title': 'アイドル DIY',
  }])
  def test_adult_optimizer_does_nothing_if_adult_tokens_in_title_but_category_is_not_adult(
      self, is_adult, test_google_product_category, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'adult': is_adult,
            'googleProductCategory': test_google_product_category,
            'title': test_title
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(False, product['adult'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'Home Garden Category',
      'is_adult': False,
      'test_description': 'グラビア 器具',
      'test_google_product_category':
          'ホーム・ガーデン > キッチン・ダイニング > '
          '調理器具',
  }, {
      'testcase_name': 'DIY Category',
      'is_adult': False,
      'test_description': 'アイドル DIY',
      'test_google_product_category': 'DIY用品 > DIY小物類',
  }])
  def test_adult_optimizer_does_nothing_if_adult_tokens_in_description_but_category_is_not_adult(
      self, is_adult, test_description, test_google_product_category):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'adult': is_adult,
            'description': test_description,
            'googleProductCategory': test_google_product_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(False, product['adult'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'Idol Category',
      'is_adult': True,
      'test_product_types': ['CD・DVD, Blu-ray', 'アイドル', 'その他'],
  }])
  def test_adult_optimizer_does_nothing_if_adult_already_set(
      self, is_adult, test_product_types):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'adult': is_adult,
            'productTypes': test_product_types
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(True, product['adult'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)
