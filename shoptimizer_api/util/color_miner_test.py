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
"""Unit tests for color_miner.py."""

from typing import Any, Dict, List, Optional
import unittest.mock as mock

from absl.testing import parameterized

from util import app_util
from util import color_miner


def _build_dummy_product(
    properties_to_be_updated: Optional[Dict[str, Any]] = None,
    properties_to_be_removed: Optional[List[str]] = None) -> Dict[str, Any]:
  """Builds a dummy product data.

  Args:
    properties_to_be_updated: The properties of a product and their values to be
      updated in a request body.
    properties_to_be_removed: The properties of a product that should be
      removed.

  Returns:
    A dummy product data.
  """
  product = {
      'color': '',
      'title': '',
      'description': '',
      'googleProductCategory': 'Apparel & Accessories',
  }

  if properties_to_be_updated:
    for key, value in properties_to_be_updated.items():
      product[key] = value

  if properties_to_be_removed:
    for key in properties_to_be_removed:
      if key in product:
        del product[key]

  return product


@mock.patch('util.color_miner._CONFIG_FILE_PATH',
            '../config/color_optimizer_config_{}_test.json')
class ColorMinerTest(parameterized.TestCase):

  def setUp(self):
    super(ColorMinerTest, self).setUp()
    app_util.setup_test_app()

  @parameterized.named_parameters([
      {
          'testcase_name':
              'mines_from_color',
          'product':
              _build_dummy_product(properties_to_be_updated={'color': '青'}),
          'expected_standard_colors': ['青'],
          'expected_unique_colors': ['青']
      },
      {
          'testcase_name':
              'mines_from_title',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={
                      'title': 'タイトルレッド青空'
                  }),
          'expected_standard_colors': ['レッド'],
          'expected_unique_colors': ['レッド']
      },
      {
          'testcase_name':
              'mines_two_colors_from_title',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={
                      'title': 'タイトルレッド・オレンジ'
                  }),
          'expected_standard_colors': ['レッド', 'オレンジ'],
          'expected_unique_colors': ['レッド', 'オレンジ']
      },
      {
          'testcase_name':
              'mines_three_colors_from_title',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={
                      'title':
                          'タイトルレッド・オレンジ・ブルー'
                  }),
          'expected_standard_colors': [
              'レッド', 'オレンジ', 'ブルー'
          ],
          'expected_unique_colors': ['レッド', 'オレンジ', 'ブルー']
      },
      {
          'testcase_name':
              'mines_from_description',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={
                      'title': '',
                      'description': '詳細赤青空'
                  }),
          'expected_standard_colors': ['赤'],
          'expected_unique_colors': ['赤']
      },
  ])
  def test_mine_color_mines_color_with_language_ja(self, product,
                                                   expected_standard_colors,
                                                   expected_unique_colors):
    miner = color_miner.ColorMiner(language='ja')

    mined_standard_color, mined_unique_color = miner.mine_color(product)

    self.assertCountEqual(expected_standard_colors, mined_standard_color)
    self.assertCountEqual(expected_unique_colors, mined_unique_color)

  @parameterized.named_parameters([
      {
          'testcase_name':
              'mines_from_color',
          'product':
              _build_dummy_product(properties_to_be_updated={'color': 'Blue'}),
          'expected_standard_colors': ['Blue'],
          'expected_unique_colors': ['Blue']
      },
      {
          'testcase_name':
              'mines_from_title',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={'title': 'Title Red'}),
          'expected_standard_colors': ['Red'],
          'expected_unique_colors': ['Red']
      },
      {
          'testcase_name':
              'mines_two_colors_from_title',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={'title': 'Title Red Green'}),
          'expected_standard_colors': ['Red', 'Green'],
          'expected_unique_colors': ['Red', 'Green']
      },
      {
          'testcase_name':
              'mines_from_description',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={
                      'title': '',
                      'description': 'Description Green'
                  }),
          'expected_standard_colors': ['Green'],
          'expected_unique_colors': ['Green']
      },
  ])
  def test_mine_color_mines_color_with_language_en(self, product,
                                                   expected_standard_colors,
                                                   expected_unique_colors):
    miner = color_miner.ColorMiner(language='en')

    mined_standard_color, mined_unique_color = miner.mine_color(product)

    self.assertCountEqual(expected_standard_colors, mined_standard_color)
    self.assertCountEqual(expected_unique_colors, mined_unique_color)

  @parameterized.named_parameters([
      {
          'testcase_name':
              'mines_from_color',
          'product':
              _build_dummy_product(
                  properties_to_be_updated={'color': 'xanh nước biển'}),
          'expected_standard_colors': ['xanh nước biển'],
          'expected_unique_colors': ['xanh nước biển'],
      },
      {
          'testcase_name':
              'mines_from_title',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={'title': 'Title màu đỏ'}),
          'expected_standard_colors': ['Màu Đỏ'],
          'expected_unique_colors': ['Màu Đỏ'],
      },
      {
          'testcase_name':
              'mines_two_colors_from_title',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={
                      'title': 'Title màu đỏ xanh lá cây',
                  }),
          'expected_standard_colors': ['Màu Đỏ', 'Xanh Lá Cây'],
          'expected_unique_colors': ['Màu Đỏ', 'Xanh Lá Cây'],
      },
      {
          'testcase_name':
              'mines_from_description',
          'product':
              _build_dummy_product(
                  properties_to_be_removed=['color'],
                  properties_to_be_updated={
                      'title': '',
                      'description': 'Description xanh lá cây',
                  }),
          'expected_standard_colors': ['Xanh Lá Cây'],
          'expected_unique_colors': ['Xanh Lá Cây'],
      },
  ])
  def test_mine_color_mines_color_with_language_vi(self, product,
                                                   expected_standard_colors,
                                                   expected_unique_colors):
    miner = color_miner.ColorMiner(language='vi')

    mined_standard_color, mined_unique_color = miner.mine_color(product)

    self.assertCountEqual(expected_standard_colors, mined_standard_color)
    self.assertCountEqual(expected_unique_colors, mined_unique_color)

  def test_mine_color_mines_three_colors_from_title_including_four_colors(self):
    miner = color_miner.ColorMiner(language='ja')
    product = _build_dummy_product(
        properties_to_be_removed=['color'],
        properties_to_be_updated={
            'title':
                'タイトル・レッド・オレンジ・ブルー・グリーン'
        })

    mined_standard_color, mined_unique_color = miner.mine_color(product)

    self.assertLen(mined_standard_color, 3)
    self.assertLen(mined_unique_color, 3)

  @parameterized.named_parameters([{
      'testcase_name': 'string',
      'category': 'Software'
  }, {
      'testcase_name': 'number',
      'category': '123456'
  }])
  def test_mine_color_does_not_mine_from_text_when_google_product_category_is_invalid(
      self, category):
    product = _build_dummy_product(
        properties_to_be_removed=['color'],
        properties_to_be_updated={
            'title': 'タイトルレッド',
            'description': '詳細赤',
            'googleProductCategory': category
        })

    miner = color_miner.ColorMiner(language='ja')

    mined_standard_color, mined_unique_color = miner.mine_color(product)

    self.assertEqual(None, mined_standard_color)
    self.assertEqual(None, mined_unique_color)
