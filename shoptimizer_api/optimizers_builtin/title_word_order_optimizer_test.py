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

"""Unit tests for title_word_order_optimizer."""

from absl.testing import parameterized
import unittest.mock as mock

from optimizers_builtin import title_word_order_optimizer
from test_data import requests_bodies
from util import app_util

import constants

# GPC ID IS 201
_PROPER_GPC_CATEGORY_EN = 'Apparel & Accessories > Jewelry > Watches'

# GPC ID is 201
_PROPER_GPC_CATEGORY_JA = ('ファッション・アクセサリー > '
                           'ジュエリー > 腕時計')
# GPC ID is 5598
_GPC_CATEGORY_LEVEL_4_JA = ('ファッション・アクセサリー > '
                            '衣料品 > アウター > '
                            'コート・ジャケット')
_MAX_WMM_MOVE_THRESHOLD_EN = 25
_MAX_WMM_MOVE_THRESHOLD_JP = 12


@mock.patch(
    'optimizers_builtin.title_word_order_optimizer._GCP_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME',
    'gpc_string_to_id_mapping_{}_test')
@mock.patch(
    'optimizers_builtin.title_word_order_optimizer._TITLE_WORD_ORDER_CONFIG_FILE_NAME',
    'title_word_order_config_{}_test')
@mock.patch(
    'optimizers_builtin.title_word_order_optimizer._TITLE_WORD_ORDER_BLOCKLIST_FILE_NAME',
    'title_word_order_blocklist_{}_test')
@mock.patch(
    'optimizers_builtin.title_word_order_optimizer._TITLE_WORD_ORDER_OPTIONS_FILE_NAME',
    'title_word_order_options_test')
class TitleWordOrderOptimizerTest(parameterized.TestCase):

  def setUp(self):
    super(TitleWordOrderOptimizerTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = title_word_order_optimizer.TitleWordOrderOptimizer()

  def test_process_copies_highest_performing_keyword_to_front_of_title(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Some title with heavy_keyword in the middle',
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    expected_title = ('[heavy_keyword] Some title with heavy_keyword in the '
                      'middle')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_copies_multiple_performing_keywords_to_front_of_title(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Some title with multiple keywords heavy_keyword '
                     'heavy_keyword_2 in the middle',
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    expected_title = (
        '[heavy_keyword_2][heavy_keyword] Some title with multiple keywords '
        'heavy_keyword heavy_keyword_2 in the middle')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_copies_multiple_performing_keywords_to_front_of_title_in_descending_order_of_weight(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'Some title with multiple keywords keyword2 keyword1 in the '
                'middle',
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    expected_title = (
        '[keyword1][keyword2] Some title with multiple keywords keyword2 '
        'keyword1 in the middle')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_copies_at_most_three_performing_keywords_to_front_of_title(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Some title with multiple keywords keyword2 keyword1 '
                     'heavy_keyword heavy_keyword_2 in the middle',
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    expected_title = (
        '[keyword1][keyword2][heavy_keyword_2] Some title with multiple '
        'keywords keyword2 keyword1 heavy_keyword heavy_keyword_2 in the '
        'middle')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_does_not_modify_title_when_the_google_product_category_is_not_in_the_config(
      self):
    original_title = 'Some title with heavy_keyword in the middle'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Some title with heavy_keyword in the middle',
            'googleProductCategory': 'DIY用品 > DIY小物類',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_modify_title_when_the_google_product_category_is_in_the_config_but_no_keywords(
      self):
    original_title = 'Some title with no target keywords in the middle'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Some title with no target keywords in the middle',
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_moves_keyword_if_title_more_than_max_title_length(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'a' * (title_word_order_optimizer._MAX_TITLE_LENGTH -
                       len(' heavy_keyword')) + ' heavy_keyword',
            'googleProductCategory':
                _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    expected_title = '[heavy_keyword] ' + 'a' * (
        title_word_order_optimizer._MAX_TITLE_LENGTH - len(' heavy_keyword'))
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_skips_one_character_wmm_keyword(self):
    original_title = 'a' * _MAX_WMM_MOVE_THRESHOLD_EN + (
        ('Some title with single a character keyword'))
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name':
          'partial_match',
      'original_title':
          'a' * _MAX_WMM_MOVE_THRESHOLD_JP + '有名ブランドTシャツ',
      'expected_title':
          'a' * _MAX_WMM_MOVE_THRESHOLD_JP + '有名ブランドTシャツ'
  }, {
      'testcase_name':
          'accurate_match',
      'original_title':
          'a' * _MAX_WMM_MOVE_THRESHOLD_JP + ' 有名ブランドシャツ',
      'expected_title':
          '[シャツ] ' + 'a' * _MAX_WMM_MOVE_THRESHOLD_JP +
          ' 有名ブランドシャツ'
  }])
  def test_wmm_keyword_is_copied_only_with_accurate_match(
      self, original_title, expected_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, _ = self.optimizer.process(original_data,
                                               constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(expected_title, product['title'])

  @parameterized.named_parameters([{
      'testcase_name': 'one_word_excluded_then_added_back',
      'original_title':
          'レッド・スニーカー、ブランド： '
          'カイナ、モデル：エオファース、色：レッド',
      'expected_title':
          '[カイナ][エオファース] '
          'レッド・スニーカー、ブランド： '
          'カイナ、モデル：エオファース、色：レッド'
  }, {
      'testcase_name':
          'keyword_already_inside_no_change_to_title',
      'original_title':
          'レッド・、カイナ,スニーカー,ブランド：、色：レッド',
      'expected_title':
          'レッド・、カイナ,スニーカー,ブランド：、色：レッド'
  }, {
      'testcase_name': 'keyword_in_first_12_char_of_the_title_jp',
      'original_title':
          'カイナレッド・スニーカー、ブランド： '
          'モデル：エオファース、色：レッド',
      'expected_title':
          '[エオファース] '
          'カイナレッド・スニーカー、ブランド： '
          'モデル：エオファース、色：レッド'
  }])
  def test_scenario_jp_wmm_keyword_in_first_12_char_of_title(
      self, original_title, expected_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, _ = self.optimizer.process(original_data,
                                               constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(expected_title, product['title'])

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._should_include_description',
      return_value=True)
  def test_wmm_keyword_in_description_is_copied_to_title_when_options_toggle_is_on(
      self, _):
    description = 'とても良い カイナ とても良い'
    original_title = ('レッド・スニーカー、ブランド： '
                      '色：レッド')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'description': description,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, _ = self.optimizer.process(original_data,
                                               constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']
    expected_title = ('[カイナ] '
                      'レッド・スニーカー、ブランド： '
                      '色：レッド')
    self.assertEqual(expected_title, product['title'])

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._should_include_description',
      return_value=False)
  def test_wmm_keyword_in_description_is_not_copied_when_options_toggle_is_off(
      self, _):
    description = 'とても良い カイナ とても良い'
    original_title = ('レッド・スニーカー、ブランド： '
                      '、色：レッド')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'description': description,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'wmm_word_in_product_type_should_move_to_front_title',
      'original_title': 'レッド・スニーカー、ブランド： '
                        'モデル：エオファース、色：レッド',
      'product_types': ['シャツ'],
      'expected_title': '[シャツ][エオファース] '
                        'レッド・スニーカー、ブランド： '
                        'モデル：エオファース、色：レッド'
  }, {
      'testcase_name': 'wmm_word_in_product_type_list_move_to_front_title',
      'original_title': 'レッド・スニーカー、ブランド： '
                        'モデル：エオファース、色：レッド',
      'product_types': ['シャツ', 'セーター', 'ジャケット'],
      'expected_title': '[シャツ][エオファース] '
                        'レッド・スニーカー、ブランド： '
                        'モデル：エオファース、色：レッド'
  }])
  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._should_include_product_types',
      return_value=True)
  def test_wmm_keyword_in_product_type_is_copied_to_title_when_options_toggle_is_on(
      self, _, original_title, product_types, expected_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'productTypes': product_types,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, _ = self.optimizer.process(original_data,
                                               constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']
    self.assertEqual(expected_title, product['title'])

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._should_include_product_types',
      return_value=False)
  def test_wmm_keyword_in_product_type_is_not_copied_to_title_when_options_toggle_is_off(
      self, _):
    original_title = ('レッド・スニーカー、ブランド： '
                      '色：レッド')
    product_types = ['シャツ']
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'productTypes': product_types,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, _ = self.optimizer.process(original_data,
                                               constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']
    self.assertEqual(original_title, product['title'])

  @parameterized.named_parameters([{
      'testcase_name':
          'japanese_title',
      'original_title':
          'a' * _MAX_WMM_MOVE_THRESHOLD_JP + 'タイトルブロック'
  }, {
      'testcase_name': 'check_case_insensitive',
      'original_title': 'a' * _MAX_WMM_MOVE_THRESHOLD_JP + 'Title Block'
  }])
  def test_wmm_keyword_in_blocklist_is_not_copied_to_front(
      self, original_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._get_optimization_level',
      return_value=title_word_order_optimizer._OptimizationLevel.AGGRESSIVE)
  def test_keywords_in_gpc_level_3_is_copied_to_front_when_gpc_level_is_deeper_than_3_and_optimization_level_is_aggressive(
      self, _):
    original_title = '寒い冬からあなたを守る！モデル：ジャケット、カラー：ブラック、防寒仕様ダウンジャケット'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _GPC_CATEGORY_LEVEL_4_JA
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    expected_title = f'[防寒][ダウンジャケット] {original_title}'
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._get_optimization_level',
      return_value=title_word_order_optimizer._OptimizationLevel.STANDARD)
  def test_optimization_is_skipped_when_gpc_level_is_deeper_than_3_and_optimization_level_is_standard(
      self, _):
    original_title = '寒い冬からあなたを守る！モデル：ジャケット、カラー：ブラック、防寒仕様ダウンジャケット'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _GPC_CATEGORY_LEVEL_4_JA
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)
