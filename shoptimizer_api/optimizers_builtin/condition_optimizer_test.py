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

"""Unit tests for condition_optimizer.py."""

import unittest.mock as mock

from absl.testing import parameterized

import constants
from optimizers_builtin import condition_optimizer
from test_data import requests_bodies
from util import app_util


@mock.patch.dict('os.environ', {'LANGUAGE': 'TEST'})
@mock.patch(
    'optimizers_builtin.condition_optimizer._GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME',
    'gpc_string_to_id_mapping_{}_test')
class ConditionOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(ConditionOptimizerTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = condition_optimizer.ConditionOptimizer()

  @parameterized.named_parameters([{
      'testcase_name': 'used',
      'test_title': '【中古】新しい商品だよ？'
  }, {
      'testcase_name': 'used 2',
      'test_title': '中古品 新しい商品だよ？'
  }, {
      'testcase_name': 'used 3',
      'test_title': '【Used】 新しい商品だよ？'
  }, {
      'testcase_name': 'unused',
      'test_title': '未使用 新しい商品だよ？'
  }, {
      'testcase_name': 'no problem',
      'test_title': '問題ない商品 新しい商品だよ？'
  }, {
      'testcase_name': 'display 1',
      'test_title': '展示品 新しい商品だよ？'
  }, {
      'testcase_name': 'display 2',
      'test_title': '展示処分 新しい商品だよ？'
  }, {
      'testcase_name': 'like new',
      'test_title': '新品同様 新しい商品だよ？'
  }, {
      'testcase_name': 'unopened',
      'test_title': '未開封 新しい商品だよ？'
  }, {
      'testcase_name': 'beautiful condition',
      'test_title': '美品 新しい商品だよ？'
  }, {
      'testcase_name': 'some reason',
      'test_title': '【訳あり】 新しい商品だよ？'
  }])
  def test_condition_optimizer_sets_new_product_to_used_based_on_title(
      self, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': test_title})

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('used', product['condition'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'used',
      'test_description': '【中古】新しい商品だよ？'
  }, {
      'testcase_name': 'used 2',
      'test_description': '中古品 新しい商品だよ？'
  }, {
      'testcase_name': 'used 3',
      'test_description': '【Used】 新しい商品だよ？'
  }, {
      'testcase_name': 'unused',
      'test_description': '未使用 新しい商品だよ？'
  }, {
      'testcase_name': 'no problem',
      'test_description': '問題ない商品 新しい商品だよ？'
  }, {
      'testcase_name': 'display 1',
      'test_description': '展示品 新しい商品だよ？'
  }, {
      'testcase_name': 'display 2',
      'test_description': '展示処分 新しい商品だよ？'
  }, {
      'testcase_name': 'like new',
      'test_description': '新品同様 新しい商品だよ？'
  }, {
      'testcase_name': 'unopened',
      'test_description': '未開封 新しい商品だよ？'
  }, {
      'testcase_name': 'beautiful condition',
      'test_description': '美品 新しい商品だよ？'
  }, {
      'testcase_name': 'some reason',
      'test_description': '【訳あり】  新しい商品だよ？'
  }])
  def test_condition_optimizer_sets_new_product_to_used_based_on_description(
      self, test_description):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'description': test_description})

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('used', product['condition'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'trading cards',
      'test_category': '芸術・エンターテイメント > 趣味・コレクション '
                       '> コレクションアイテム > トレーディングカード',
      'test_title': 'カード名: 新しい商品だよ？'
  }, {
      'testcase_name': 'smartphones',
      'test_category': '電気製品 > 通信機器 > 電話 > '
                       '携帯電話・スマートフォン',
      'test_title': 'ロック解除済: 新しい商品だよ？'
  }])
  def test_condition_optimizer_sets_new_to_used_based_on_category_and_title(
      self, test_category, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'googleProductCategory': test_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('used', product['condition'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'trading cards',
      'test_category': 6997,
      'test_title': 'カード名: 新しい商品だよ？'
  }, {
      'testcase_name': 'smartphones',
      'test_category': 267,
      'test_title': 'ロック解除済: 新しい商品だよ？'
  }])
  def test_condition_optimizer_sets_new_to_used_based_on_gpc_id_and_title(
      self, test_category, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'googleProductCategory': test_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'ja')
    product = optimized_data['entries'][0]['product']

    self.assertEqual('used', product['condition'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'trading cards',
      'test_category': '芸術・エンターテイメント > 趣味・コレクション '
                       '> コレクションアイテム > トレーディングカード',
      'test_description': 'カード名: 新しい商品だよ？'
  }, {
      'testcase_name': 'smartphones',
      'test_category': '電気製品 > 通信機器 > 電話 > '
                       '携帯電話・スマートフォン',
      'test_description': 'ロック解除済: 新しい商品だよ？'
  }])
  def test_condition_optimizer_sets_new_to_used_based_on_category_and_description(
      self, test_category, test_description):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': test_description,
            'googleProductCategory': test_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('used', product['condition'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'default',
      'test_title': '新しい商品だよ？'
  }, {
      'testcase_name': 'out',
      'test_title': 'アウト 新しい商品だよ？'
  }, {
      'testcase_name': 'product',
      'test_title': '商品 新しい商品だよ？'
  }, {
      'testcase_name': 'sell',
      'test_title': '売り 新しい商品だよ？'
  }, {
      'testcase_name': 'in use',
      'test_title': '使用 新しい商品だよ？'
  }, {
      'testcase_name': 'problem',
      'test_title': '問題 新しい商品だよ？'
  }, {
      'testcase_name': 'exhibition',
      'test_title': '展示会 新しい商品だよ？'
  }, {
      'testcase_name': 'new',
      'test_title': '新品 新しい商品だよ？'
  }, {
      'testcase_name': 'box',
      'test_title': '箱 新しい商品だよ？'
  }, {
      'testcase_name': 'beautiful',
      'test_title': '美 新しい商品だよ？'
  }, {
      'testcase_name': 'good',
      'test_title': '良 新しい商品だよ？'
  }, {
      'testcase_name': 'wrapped',
      'test_title': '梱包 新しい商品だよ？'
  }, {
      'testcase_name': 'sold',
      'test_title': '売品 新しい商品だよ？'
  }])
  def test_condition_optimizer_doesnt_change_condition_based_no_matches_in_title(
      self, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': test_title})

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('new', product['condition'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'default',
      'test_description': '新しい商品だよ？'
  }, {
      'testcase_name': 'out',
      'test_description': 'アウト 新しい商品だよ？'
  }, {
      'testcase_name': 'product',
      'test_description': '商品 新しい商品だよ？'
  }, {
      'testcase_name': 'sell',
      'test_description': '売り 新しい商品だよ？'
  }, {
      'testcase_name': 'in use',
      'test_description': '使用 新しい商品だよ？'
  }, {
      'testcase_name': 'problem',
      'test_description': '問題 新しい商品だよ？'
  }, {
      'testcase_name': 'exhibition',
      'test_description': '展示会 新しい商品だよ？'
  }, {
      'testcase_name': 'new',
      'test_description': '新品 新しい商品だよ？'
  }, {
      'testcase_name': 'box',
      'test_description': '箱 新しい商品だよ？'
  }, {
      'testcase_name': 'beautiful',
      'test_description': '美 新しい商品だよ？'
  }, {
      'testcase_name': 'good',
      'test_description': '良 新しい商品だよ？'
  }, {
      'testcase_name': 'wrapped',
      'test_description': '梱包 新しい商品だよ？'
  }, {
      'testcase_name': 'sold',
      'test_description': '売品 新しい商品だよ？'
  }])
  def test_condition_optimizer_doesnt_change_condition_based_no_matches_in_description(
      self, test_description):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'description': test_description})

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('new', product['condition'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'trading cards',
      'test_category': '芸術・エンターテイメント > 趣味・コレクション '
                       '> コレクションアイテム > トレーディングカード',
      'test_title': 'カード: 新しい商品だよ？'
  }, {
      'testcase_name': 'smartphones',
      'test_category': '電気製品 > 通信機器 > 電話 > '
                       '携帯電話・スマートフォン',
      'test_title': 'ロック: 新しい商品だよ？'
  }])
  def test_condition_optimizer_doesnt_change_condition_based_on_category_and_no_matches_in_title(
      self, test_category, test_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': test_title,
            'googleProductCategory': test_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('new', product['condition'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'trading cards',
      'test_category': '芸術・エンターテイメント > 趣味・コレクション > コレクションアイテム > トレーディングカード',
      'test_description': 'カード: 新しい商品だよ？'
  }, {
      'testcase_name': 'smartphones',
      'test_category': '電気製品 > 通信機器 > 電話 > 携帯電話・スマートフォン',
      'test_description': 'ロック: 新しい商品だよ？'
  }])
  def test_condition_optimizer_doesnt_change_condition_based_on_category_and_no_matches_in_description(
      self, test_category, test_description):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': test_description,
            'googleProductCategory': test_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('new', product['condition'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([{
      'testcase_name': 'books',
      'test_category': 'メディア > 書籍',
      'test_description': '本: 中古商品だよ？'
  }])
  def test_condition_optimizer_doesnt_change_condition_based_on_excluded_category(
      self, test_category, test_description):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': test_description,
            'googleProductCategory': test_category
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)
    product = optimized_data['entries'][0]['product']

    self.assertEqual('new', product['condition'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)
