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
from typing import List, Dict
from util import app_util

import constants

# GPC ID IS 201
_PROPER_GPC_CATEGORY_EN = 'Apparel & Accessories > Jewelry > Watches'

# GPC ID is 201
_PROPER_GPC_CATEGORY_JA = ('ファッション・アクセサリー > ' 'ジュエリー > 腕時計')
# GPC ID is 5598
_GPC_CATEGORY_LEVEL_4_JA = ('ファッション・アクセサリー > ' '衣料品 > アウター > ' 'コート・ジャケット')


@mock.patch('util.promo_text_remover._PROMO_TEXT_REMOVAL_CONFIG_FILE_NAME',
            'promo_text_removal_optimizer_config_{}_test')
@mock.patch(
    'optimizers_builtin.title_word_order_optimizer._GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME',
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
    title_word_order_optimizer.CUSTOM_TEXT_TOKENIZER = None
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
    original_title = 'a' * constants.TITLE_CHARS_VISIBLE_TO_USER_EN + (
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
          'a' * constants.TITLE_CHARS_VISIBLE_TO_USER_JA + '有名ブランドTシャツ',
      'expected_title':
          'a' * constants.TITLE_CHARS_VISIBLE_TO_USER_JA + '有名ブランドTシャツ'
  }, {
      'testcase_name':
          'accurate_match',
      'original_title':
          'a' * constants.TITLE_CHARS_VISIBLE_TO_USER_JA + ' 有名ブランドシャツ',
      'expected_title':
          '[シャツ] ' + 'a' * constants.TITLE_CHARS_VISIBLE_TO_USER_JA +
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
      'original_title': 'レッド・スニーカー、ブランド： '
                        'カイナ、モデル：エオファース、色：レッド',
      'expected_title': '[カイナ][エオファース] '
                        'レッド・スニーカー、ブランド： '
                        'カイナ、モデル：エオファース、色：レッド'
  }, {
      'testcase_name':
          'keyword_kaina_already_within_japanese_threshold_chars_no_change_to_title',
      'original_title':
          'レッド・、カイナ,スニーカー,ブランド：、色：レッド',
      'expected_title':
          'レッド・、カイナ,スニーカー,ブランド：、色：レッド'
  }, {
      'testcase_name':
          'keyword_kaina_right_at_the_limit_of_japanese_threshold_chars_no_change_to_title',
      'original_title':
          'レッド・レッド123レッド1,カイナ,ブランド：、色：レッド',
      'expected_title':
          'レッド・レッド123レッド1,カイナ,ブランド：、色：レッド'
  }, {
      'testcase_name':
          'keyword_kaina_is_partially_in_the_japanese_threshold_chars_and_partially_out_we_copy_it_to_front_title',
      'original_title':
          'レッド2・レッド1,レッド321,カイナ,ブランド：、色：レッド',
      'expected_title':
          '[カイナ] '
          'レッド2・レッド1,レッド321,カイナ,ブランド：、色：レッド'
  }, {
      'testcase_name':
          'keyword_kaina_is_right_out_of_the_japanese_threshold_chars_we_copy_it_to_front_title',
      'original_title':
          'レッド21・レッド12,レッド12,カイナ,ブランド：、色：レッド',
      'expected_title':
          '[カイナ] '
          'レッド21・レッド12,レッド12,カイナ,ブランド：、色：レッド'
  }])
  def test_scenario_jp_wmm_keyword_in_first_18_char_of_title(
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
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._optimization_includes_description',
      return_value=True)
  def test_wmm_keyword_in_description_is_copied_to_title_when_options_toggle_is_on(
      self, _):
    description = 'とても良い カイナ とても良い'
    original_title = ('レッド・スニーカー、ブランド： ' '色：レッド')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'description': description,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, _ = self.optimizer.process(original_data,
                                               constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']
    expected_title = ('[カイナ] ' 'レッド・スニーカー、ブランド： ' '色：レッド')
    self.assertEqual(expected_title, product['title'])

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._optimization_includes_description',
      return_value=False)
  def test_wmm_keyword_in_description_is_not_copied_when_options_toggle_is_off(
      self, _):
    description = 'とても良い カイナ とても良い'
    original_title = ('レッド・スニーカー、ブランド： ' '、色：レッド')
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
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._optimization_includes_product_types',
      return_value=True)
  def test_wmm_keyword_in_product_types_is_copied_to_title_when_options_toggle_is_on(
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
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._optimization_includes_product_types',
      return_value=False)
  def test_wmm_keyword_in_product_types_is_not_copied_to_title_when_options_toggle_is_off(
      self, _):
    original_title = ('レッド・スニーカー、ブランド： ' '色：レッド')
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
          'a' * constants.TITLE_CHARS_VISIBLE_TO_USER_JA + 'タイトルブロック'
  }, {
      'testcase_name':
          'check_case_insensitive',
      'original_title':
          'a' * constants.TITLE_CHARS_VISIBLE_TO_USER_JA + 'Title Block'
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

  @parameterized.named_parameters([{
      'testcase_name': 'japanese_title_hiroo_mobile_should_move_to_front',
      'original_title': 'あなたの携帯電話のために最高の取引をしたいですか？広尾 モバイルを使う'
  }])
  def test_dictionary_term_file_tokenizes_japanese_title_properly(
      self, original_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _PROPER_GPC_CATEGORY_JA
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    expected_title = '[広尾 モバイル] あなたの携帯電話のために最高の取引をしたいですか？広尾 モバイルを使う'

    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name':
          'non_japanese_title_hiroo_mobile_should_move_to_front',
      'original_title':
          'You want the best mobile phone deal? Come get Hiroo Mobile now!'
  }])
  def test_dictionary_term_file_tokenizes_non_japanese_title_properly(
      self, original_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    expected_title = ('[Hiroo Mobile] You want the best mobile phone deal? '
                      'Come get Hiroo Mobile now!')

    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

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

  def test_process_interprets_valid_gpc_id_and_copies_performant_keyword(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Some title with heavy_keyword in the middle',
            'googleProductCategory': '201',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    expected_title = ('[heavy_keyword] Some title with heavy_keyword in the '
                      'middle')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_ignores_invalid_gpc_id_and_does_nothing(self):
    original_title = 'Some title with heavy_keyword in the middle'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': '202',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_promo_text_dont_get_move_to_the_front(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                '寒い冬からあなたを守る！モデル：ジャケット、[送料無料] , カイナ ,カラー：ブラック、防寒仕様ダウンジャケット',
            'googleProductCategory':
                _PROPER_GPC_CATEGORY_JA,
        })
    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    expected_title = ('[カイナ] '
                      '寒い冬からあなたを守る！モデル：ジャケット、[送料無料]'
                      ' , カイナ '
                      ',カラー：ブラック、防寒仕様ダウンジャケット')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._get_keywords_position',
      return_value=title_word_order_optimizer._KeywordsPosition.BACK)
  def test_keywords_are_appended_in_descending_order_of_weight_when_keywords_position_is_back(
      self, _):
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

    expected_title = ('Some title with multiple keywords keyword2 '
                      'keyword1 in the middle [keyword1][keyword2]')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._get_keywords_position',
      return_value=title_word_order_optimizer._KeywordsPosition.BACK)
  def test_at_most_three_keywords_are_appended_weight_when_keywords_position_is_back(
      self, _):
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
        'Some title with multiple '
        'keywords keyword2 keyword1 heavy_keyword heavy_keyword_2 in the '
        'middle [keyword1][keyword2][heavy_keyword_2]')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._get_keywords_position',
      return_value=title_word_order_optimizer._KeywordsPosition.BACK)
  def test_title_is_not_optimized_if_title_more_than_max_title_length_when_keywords_position_is_back(
      self, _):
    original_title = 'a' * (title_word_order_optimizer._MAX_TITLE_LENGTH -
                            len(' heavy_keyword')) + ' heavy_keyword'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @mock.patch(
      'optimizers_builtin.title_word_order_optimizer.TitleWordOrderOptimizer._get_keywords_position',
      return_value=title_word_order_optimizer._KeywordsPosition.BACK)
  def test_a_number_of_keywords_are_appended_so_that_title_length_does_not_exceed_max_length_when_keywords_position_is_back(
      self, _):
    original_title = 'a' * (title_word_order_optimizer._MAX_TITLE_LENGTH - len(
        ' keyword1 keyword2 [keyword1]')) + ' keyword1 keyword2'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    # [keyword2] is not appended.
    expected_title = 'a' * (title_word_order_optimizer._MAX_TITLE_LENGTH - len(
        ' keyword1 keyword2 [keyword1]')) + ' keyword1 keyword2 [keyword1]'
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)


def _set_test_variables(module: 'Module'):
  """Sets the module variables for testing outside a Flask environment."""
  module.GPC_STRING_TO_ID_MAPPING_CONFIG = {
      'Apparel & Accessories': 166,
      'Apparel & Accessories > Jewelry': 188,
      'Apparel & Accessories > Jewelry > Watches': 201,
  }

  module.TITLE_WORD_ORDER_CONFIG = {
      'phrase_dictionary': ['4 roses', 'Hiroo Mobile'],
      'keyword_weights_by_gpc': {
          '201': [{
              'keyword': 'keyword1',
              'weight': 0.8
          }, {
              'keyword': 'keyword2',
              'weight': 0.7
          }, {
              'keyword': 'heavy_keyword',
              'weight': 0.5
          }, {
              'keyword': 'heavy_keyword_2',
              'weight': 0.6
          }, {
              'keyword': 'a',
              'weight': 0.4
          }, {
              'keyword': 'magic',
              'weight': 0.3
          }],
          '632': [{
              'keyword': 'keyword1',
              'weight': 0.5
          }, {
              'keyword': 'keyword2',
              'weight': 0.7
          }]
      }
  }
  module.BLOCKLIST_CONFIG = {}

  module.TITLE_WORD_ORDER_OPTIONS_CONFIG = {
      'descriptionIncluded': False,
      'productTypesIncluded': False,
      'optimizationLevel': 'standard'
  }


@mock.patch(
    'optimizers_builtin.title_word_order_optimizer._TITLE_WORD_ORDER_OPTIONS_FILE_NAME',
    'title_word_order_options_test')
class TitleWordOrderOptimizerNoFlaskTest(parameterized.TestCase):
  """Tests TitleWordOrderOptimizer running outside a Flask context."""

  def setUp(self):
    super(TitleWordOrderOptimizerNoFlaskTest, self).setUp()
    # Explicitly no Flask context setup here.
    _set_test_variables(module=title_word_order_optimizer)
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

  def test_process_uses_custom_text_tokenizer(self):
    title_word_order_optimizer.CUSTOM_TEXT_TOKENIZER = _custom_text_tokenizer
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Some,title,with,heavy_keyword,with,commas',
            'googleProductCategory': _PROPER_GPC_CATEGORY_EN,
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_EN)
    product = optimized_data['entries'][0]['product']

    expected_title = (
        '[heavy_keyword] Some,title,with,heavy_keyword,with,commas')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)


def _custom_text_tokenizer(text: str, lang: str,
                           dictionary_terms: Dict[str, str]) -> List[str]:
  """Helper function to split text by a comma."""
  del lang
  del dictionary_terms
  return text.split(',')
