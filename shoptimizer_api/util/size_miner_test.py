# coding=utf-8
# Copyright 2024 Google LLC.
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

"""Unit tests for size_miner.py."""
import unittest.mock as mock

from absl.testing import parameterized
import constants
from util import app_util
from util import size_miner


@mock.patch.object(size_miner, '_GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME',
                   'gpc_string_to_id_mapping_{}_test')
class SizeMinerTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    app_util.setup_test_app()

  def test_mine_size_mines_size_from_sizes_field_with_language_ja(self):
    product = {
        'title': 'TシャツM',
        'description': 'TシャツM',
        'googleProductCategory': 'ファッション・アクセサリー > 衣料品',
        'sizes': ['L', 'S'],
    }
    miner = size_miner.SizeMiner(
        language=constants.LANGUAGE_CODE_JA, country=constants.COUNTRY_CODE_JP)

    mined_size = miner.mine_size(product)

    self.assertEqual('L', mined_size)

  @parameterized.named_parameters([{
      'testcase_name': 'empty',
      'title': '',
      'expected_size': None,
  }, {
      'testcase_name': 'standard_size',
      'title': 'Tシャツ L',
      'expected_size': 'L',
  }, {
      'testcase_name': 'standard_size_extra_large',
      'title': 'Tシャツ XXXL',
      'expected_size': 'XXXL',
  }, {
      'testcase_name': 'standard_size_large_with_false_positive',
      'title': 'SM Tシャツ L',
      'expected_size': 'L',
  }, {
      'testcase_name': 'standard_sizes_range',
      'title': 'Tシャツ S-M',
      'expected_size': 'S-M',
  }, {
      'testcase_name': 'standard_sizes_wide_range',
      'title': 'Tシャツ S-XXL',
      'expected_size': 'S-XXL',
  }, {
      'testcase_name': 'size_validates_range_in_middle_with_false_positive',
      'title': 'TシャツSサイズ:SS-XXLシャツ',
      'expected_size': 'SS-XXL',
  }, {
      'testcase_name': 'standard_sizes_multiple_slash',
      'title': 'Tシャツ S/M/L',
      'expected_size': 'S/M/L',
  }, {
      'testcase_name': 'standard_sizes_multiple_slash_with_false_positive',
      'title': 'Lシャツ S/M/L',
      'expected_size': 'S/M/L',
  }, {
      'testcase_name': 'numeric_size_ja_indicator',
      'title': 'Tシャツ サイズ：40',
      'expected_size': '40',
  }, {
      'testcase_name': 'numeric_size_decimal_ja_indicator_units',
      'title': 'Tシャツ サイズ：40.5cm',
      'expected_size': '40.5cm',
  }, {
      'testcase_name': 'numeric_size_decimal_ja_indicator_units_with_space',
      'title': 'Tシャツ サイズ：40.5 cm',
      'expected_size': '40.5cm',
  }, {
      'testcase_name': 'numeric_size_en_indicator',
      'title': 'Tシャツ Size:40',
      'expected_size': '40',
  }, {
      'testcase_name': 'size_does_not_exist',
      'title': 'Tシャツ',
      'expected_size': None,
  }, {
      'testcase_name': 'size_indicated_but_value_missing',
      'title': 'Tシャツ サイズ：N/A',
      'expected_size': None,
  }, {
      'testcase_name': 'size_multiple_values_only_first',
      'title': 'Tシャツ サイズ：10.5cm 11.5cm',
      'expected_size': '10.5cm',
  }, {
      'testcase_name': 'size_range_is_valid',
      'title': 'Tシャツ サイズ：10.5-11.5cm',
      'expected_size': '10.5-11.5cm',
  }, {
      'testcase_name': 'size_skips_nonsize_after_indicator',
      'title': 'Tシャツ モデルサイズ:身長:160cm',
      'expected_size': '160cm',
  }, {
      'testcase_name': 'size_validates_inches',
      'title': 'Tシャツ サイズ: 10 in shirt',
      'expected_size': '10in',
  }, {
      'testcase_name': 'size_validates_years',
      'title': 'Tシャツ サイズ: 10歳',
      'expected_size': '10歳',
  }, {
      'testcase_name': 'unisize',
      'title': 'フリーサイズ 40L',
      'expected_size': 'フリーサイズ',
  }])
  def test_mine_size_mines_clothing_size_from_title_with_language_ja(
      self, title, expected_size):
    product = {
        'title': title,
        'description': '',
        'googleProductCategory': 'ファッション・アクセサリー > 衣料品',
        'sizes': [],
    }
    miner = size_miner.SizeMiner(
        language=constants.LANGUAGE_CODE_JA, country=constants.COUNTRY_CODE_JP)

    mined_size = miner.mine_size(product)

    self.assertEqual(expected_size, mined_size)

  @parameterized.named_parameters([{
      'testcase_name': 'empty',
      'title': '',
      'expected_size': None,
  }, {
      'testcase_name': 'one_word_size',
      'title': 'T-Shirt L',
      'expected_size': 'L',
  }, {
      'testcase_name': 'multiple_words_size',
      'title': 'T-Shirt One size fits all',
      'expected_size': 'One size fits all',
  }, {
      'testcase_name': 'unisize_is_prioritized',
      'title': 'T-Shirt One size fits all L',
      'expected_size': 'One size fits all',
  }, {
      'testcase_name': 'size_not_exist',
      'title': 'T-Shirt',
      'expected_size': None,
  }])
  def test_mine_size_mines_clothing_size_from_title_with_language_en(
      self, title, expected_size):
    product = {
        'title': title,
        'description': '',
        'googleProductCategory': 'Apparel & Accessories > Clothing',
        'sizes': [],
    }
    miner = size_miner.SizeMiner(
        language=constants.LANGUAGE_CODE_EN, country=constants.COUNTRY_CODE_US)

    mined_size = miner.mine_size(product)

    self.assertEqual(expected_size, mined_size)

  @parameterized.named_parameters([{
      'testcase_name': 'empty',
      'title': '',
      'expected_size': None,
  }, {
      'testcase_name': 'one_word_size',
      'title': 'T-Shirt L',
      'expected_size': 'L',
  }, {
      'testcase_name': 'multiple_words_size',
      'title': 'T-Shirt One size fits all',
      'expected_size': 'One size fits all',
  }, {
      'testcase_name': 'unisize_is_prioritized',
      'title': 'T-Shirt One size fits all L',
      'expected_size': 'One size fits all',
  }, {
      'testcase_name': 'size_not_exist',
      'title': 'T-Shirt',
      'expected_size': None,
  }])
  def test_mine_size_mines_clothing_size_from_title_with_language_en_and_gpc_number(
      self, title, expected_size):
    product = {
        'title': title,
        'description': '',
        'googleProductCategory': 1604,
        'sizes': [],
    }
    miner = size_miner.SizeMiner(
        language=constants.LANGUAGE_CODE_EN, country=constants.COUNTRY_CODE_US)

    mined_size = miner.mine_size(product)

    self.assertEqual(expected_size, mined_size)

  @parameterized.named_parameters([{
      'testcase_name': 'empty',
      'description': '',
      'expected_size': None,
  }, {
      'testcase_name': 'standard_size',
      'description': 'Tシャツ L',
      'expected_size': 'L',
  }, {
      'testcase_name': 'size_keyword',
      'description': 'Tシャツ サイズ：40',
      'expected_size': '40',
  }, {
      'testcase_name': 'standard_size_is_not_prioritized',
      'description': 'Tシャツ サイズ:40L',
      'expected_size': '40L',
  }, {
      'testcase_name': 'size_not_exist',
      'description': 'Tシャツ',
      'expected_size': None,
  }])
  def test_mine_size_mines_clothing_size_from_description_with_language_ja(
      self, description, expected_size):
    product = {
        'title': '',
        'description': description,
        'googleProductCategory': 'ファッション・アクセサリー > 衣料品',
        'sizes': [],
    }
    miner = size_miner.SizeMiner(
        language=constants.LANGUAGE_CODE_JA, country=constants.COUNTRY_CODE_JP)

    mined_size = miner.mine_size(product)

    self.assertEqual(expected_size, mined_size)

  @parameterized.named_parameters([{
      'testcase_name': 'empty',
      'description': '',
      'expected_size': None,
  }, {
      'testcase_name': 'one_word_size_l',
      'description': 'T-Shirt L',
      'expected_size': 'L',
  }, {
      'testcase_name': 'one_word_size_large',
      'description': 'T-Shirt Large',
      'expected_size': 'Large',
  }, {
      'testcase_name': 'multiple_words_size',
      'description': 'T-Shirt One size fits all',
      'expected_size': 'One size fits all',
  }, {
      'testcase_name': 'unisize_is_prioritized',
      'description': 'T-Shirt One size fits all L',
      'expected_size': 'One size fits all',
  }, {
      'testcase_name': 'size_not_exist',
      'description': 'T-Shirt',
      'expected_size': None,
  }])
  def test_mine_size_mines_clothing_size_from_description_with_language_en(
      self, description, expected_size):
    product = {
        'title': '',
        'description': description,
        'googleProductCategory': 'ファッション・アクセサリー > 衣料品',
        'sizes': [],
    }
    miner = size_miner.SizeMiner(
        language=constants.LANGUAGE_CODE_EN, country=constants.COUNTRY_CODE_US)

    mined_size = miner.mine_size(product)

    self.assertEqual(expected_size, mined_size)

  @parameterized.named_parameters([
      {
          'testcase_name': 'empty',
          'title': '',
          'expected_size': None,
      },
      {
          'testcase_name': 'valid_size_integer',
          'title': 'スニーカー 27cm',
          'expected_size': '27',
      },
      {
          'testcase_name': 'valid_size_first_decimal_place_zero',
          'title': 'スニーカー 27.0cm',
          'expected_size': '27.0',
      },
      {
          'testcase_name': 'valid_size_first_decimal_place_five',
          'title': 'スニーカー 27.5cm',
          'expected_size': '27.5',
      },
      {
          'testcase_name': 'minimum_size',
          'title': 'スニーカー 10cm',
          'expected_size': '10',
      },
      {
          'testcase_name': 'maximum_size',
          'title': 'スニーカー 35cm',
          'expected_size': '35',
      },
      {
          'testcase_name': 'invalid_size_too_small',
          'title': 'スニーカー 9cm',
          'expected_size': None,
      },
      {
          'testcase_name': 'invalid_size_too_big',
          'title': 'スニーカー 36cm',
          'expected_size': None,
      },
      {
          'testcase_name': 'invalid_size_first_decimal_place_one',
          'title': 'スニーカー 27.1cm',
          'expected_size': None,
      },
  ])
  def test_mine_size_mines_shoes_size_from_title_with_language_ja(
      self, title, expected_size):
    product = {
        'title': title,
        'description': '',
        'googleProductCategory': 'ファッション・アクセサリー > 靴',
        'sizes': [],
    }
    miner = size_miner.SizeMiner(
        language=constants.LANGUAGE_CODE_JA, country=constants.COUNTRY_CODE_JP)

    mined_size = miner.mine_size(product)

    self.assertEqual(expected_size, mined_size)

  @parameterized.named_parameters([
      {
          'testcase_name': 'empty',
          'title': '',
          'expected_size': None,
      },
      {
          'testcase_name': 'valid_size_integer',
          'title': 'Sneaker 9',
          'expected_size': '9',
      },
      {
          'testcase_name': 'valid_size_first_decimal_place_zero',
          'title': 'Sneaker 9.0',
          'expected_size': '9.0',
      },
      {
          'testcase_name': 'valid_size_first_decimal_place_five',
          'title': 'Sneaker 9.5',
          'expected_size': '9.5',
      },
      {
          'testcase_name': 'minimum_size',
          'title': 'Sneaker 4',
          'expected_size': '4',
      },
      {
          'testcase_name': 'maximum_size',
          'title': 'Sneaker 16',
          'expected_size': '16',
      },
      {
          'testcase_name': 'invalid_size_too_small',
          'title': 'Sneaker 3',
          'expected_size': None,
      },
      {
          'testcase_name': 'invalid_size_too_big',
          'title': 'Sneaker 21',
          'expected_size': None,
      },
      {
          'testcase_name': 'invalid_size_first_decimal_place_one',
          'title': 'Sneaker 9.1',
          'expected_size': None,
      },
  ])
  def test_mine_size_mines_shoes_size_from_title_with_language_en_and_country_us(
      self, title, expected_size):
    product = {
        'title': title,
        'description': '',
        'googleProductCategory': 'Apparel & Accessories > Shoes',
        'sizes': [],
    }
    miner = size_miner.SizeMiner(
        language=constants.LANGUAGE_CODE_EN, country=constants.COUNTRY_CODE_US)

    mined_size = miner.mine_size(product)

    self.assertEqual(expected_size, mined_size)
