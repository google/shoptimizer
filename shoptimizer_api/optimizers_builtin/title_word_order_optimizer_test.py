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

from optimizers_builtin import title_word_order_optimizer
from test_data import requests_bodies
from util import app_util


class TitleWordOrderOptimizerTest(parameterized.TestCase):

  def setUp(self):
    super(TitleWordOrderOptimizerTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = title_word_order_optimizer.TitleWordOrderOptimizer()

  def test_process_copies_highest_performing_keyword_to_front_of_title(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'Some title with heavy_keyword in the middle',
            'googleProductCategory':
                'ファッション・アクセサリー > ジュエリー > 腕時計',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    expected_title = ('[heavy_keyword] Some title with heavy_keyword in the '
                      'middle')
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_copies_multiple_performing_keywords_to_front_of_title(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'Some title with multiple keywords heavy_keyword '
                'heavy_keyword_2 in the middle',
            'googleProductCategory':
                'ファッション・アクセサリー > ジュエリー > 腕時計',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
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
            'googleProductCategory':
                'ファッション・アクセサリー > ジュエリー > 腕時計',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
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
            'title':
                'Some title with multiple keywords keyword2 keyword1 '
                'heavy_keyword heavy_keyword_2 in the middle',
            'googleProductCategory':
                'ファッション・アクセサリー > ジュエリー > 腕時計',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
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
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_modify_title_when_the_google_product_category_is_in_the_config_but_no_keywords(
      self):
    original_title = 'Some title with no target keywords in the middle'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'Some title with no target keywords in the middle',
            'googleProductCategory':
                'ファッション・アクセサリー > ジュエリー > 腕時計',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
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
                'ファッション・アクセサリー > ジュエリー > 腕時計',
        })

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    expected_title = '[heavy_keyword] ' + 'a' * (
        title_word_order_optimizer._MAX_TITLE_LENGTH - len(' heavy_keyword'))
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)
