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
"""Unit tests for title_optimizer."""

import unittest.mock as mock

from absl.testing import parameterized

import constants
import enums
from optimizers_builtin import title_optimizer
from test_data import requests_bodies
from util import app_util
from util import attribute_miner


class TitleOptimizerTest(parameterized.TestCase):

  def setUp(self):
    super(TitleOptimizerTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = title_optimizer.TitleOptimizer()
    self.fields_to_append = ['gender', 'color', 'sizes', 'brand']

  def test_process_truncates_title_when_it_is_too_long(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'a' * (title_optimizer._MAX_TITLE_LENGTH * 2)
        },
        properties_to_be_removed=self.fields_to_append)

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    expected_title = 'a' * title_optimizer._MAX_TITLE_LENGTH
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_not_truncate_title_when_title_length_equal_to_the_max(self):
    original_title = 'a' * title_optimizer._MAX_TITLE_LENGTH
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': original_title},
        properties_to_be_removed=self.fields_to_append)

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters({
      'testcase_name': 'empty',
      'suffix': ''
  }, {
      'testcase_name': 'one period',
      'suffix': '.'
  }, {
      'testcase_name': 'two periods',
      'suffix': '..'
  }, {
      'testcase_name': 'three periods',
      'suffix': '...'
  }, {
      'testcase_name': 'one ellipsis',
      'suffix': '…'
  }, {
      'testcase_name': 'two ellipses',
      'suffix': '……'
  })
  def test_process_untruncate_title_when_title_is_truncated_from_description(
      self, suffix):
    original_description = 'a' * (title_optimizer._MAX_TITLE_LENGTH * 2)
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'a' * (title_optimizer._MAX_TITLE_LENGTH - 5) + suffix,
            'description': original_description
        },
        properties_to_be_removed=self.fields_to_append)

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    expected_title = (original_description[:title_optimizer._MAX_TITLE_LENGTH])
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_not_untruncate_title_when_title_not_truncated_from_description(
      self):
    original_title = 'a'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'description': 'b'
        },
        properties_to_be_removed=self.fields_to_append)

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_sets_product_tracking_field_to_optimized_when_title_optimized(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'gender': 'male',
            'googleProductCategory': 'Apparel & Accessories > Shoes'
        },
        properties_to_be_removed=['color', 'sizes'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    tracking_field = 'customLabel4'
    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = optimizer.process(original_data, 'test')
      product = optimized_data['entries'][0]['product']

      self.assertEqual(enums.TrackingTag.OPTIMIZED.value,
                       product[tracking_field])

  def test_process_appends_color_when_the_field_has_value(self):
    original_title = 'dummy title'
    self.fields_to_append.remove('color')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'color': 'Black',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertIn('Black', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_truncates_and_appends_color_when_title_too_long_after_desc_appended(
      self):
    self.fields_to_append.remove('color')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'aaaaa...',
            'description': 'a' * title_optimizer._MAX_TITLE_LENGTH,
            'color': 'Black',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Black', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_truncates_and_appends_sizes_when_title_too_long_after_desc_appended(
      self):
    self.fields_to_append.remove('sizes')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'aaaaa...',
            'description': 'a' * title_optimizer._MAX_TITLE_LENGTH,
            'sizes': ['Large'],
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Large', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters(
      {
          'testcase_name': 'short title',
          'original_title': 'dummy title',
          'expected_title': 'dummy title… Men\'s Large Google Black'
      }, {
          'testcase_name':
              'long title expanded from description',
          'original_title':
              'aaaaa...',
          'expected_title':
              'a' * (title_optimizer._MAX_TITLE_LENGTH -
                     len('… Men\'s Large Google Black')) +
              '… Men\'s Large Google Black'
      })
  def test_process_appends_multiple_field_values(self, original_title,
                                                 expected_title):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'description': 'a' * title_optimizer._MAX_TITLE_LENGTH,
            'gender': 'male',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'color': 'Black',
            'sizes': ['Large', 'Small']
        })
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_does_not_append_fields_when_values_do_not_exist(self):
    original_title = 'dummy title'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_append_fields_when_field_already_in_title(self):
    original_title = 'dummy title Black Large'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'color': 'Black',
            'sizes': ['Large']
        },
        properties_to_be_removed=['gender', 'brand'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_set_product_tracking_field_when_title_equals_description(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'Beauty product',
            'description': 'Beauty product'
        },
        properties_to_be_removed=self.fields_to_append)
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = self.optimizer.process(original_data, 'test')
      optimized_product = optimized_data['entries'][0]['product']

      self.assertEqual('', optimized_product[tracking_field])
      self.assertEqual(original_data, optimized_data)

  def test_process_does_not_change_title_if_no_space_to_append_attributes(self):
    original_title = 'a' * title_optimizer._MAX_TITLE_LENGTH
    brand_to_append = 'Cool Company'
    self.fields_to_append.remove('brand')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'brand': brand_to_append,
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_preserves_original_title(self):
    space_for_attributes = 15
    original_title = 'a' * (
        title_optimizer._MAX_TITLE_LENGTH - space_for_attributes)
    expected_title = f"{original_title}aa… Men's Large"
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'description': 'a' * title_optimizer._MAX_TITLE_LENGTH,
            'gender': 'male',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'color': 'Red',
            'sizes': ['Large', 'Small']
        })
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_title_created_from_description_if_title_does_not_exist(self):
    brand = 'Nike'
    color = 'black'
    description = 'Product that is missing a title but has a description'
    sizes = ['Large']
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'brand': brand,
            'color': color,
            'description': description,
            'sizes': sizes
        },
        properties_to_be_removed=['title'])
    expected_title = f'{description}… {sizes[0]} {brand} {color}'
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']

    self.assertEqual(expected_title, product.get('title'))
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_title_created_from_attributes_if_title_and_description_do_not_exist(
      self):
    brand = 'Nike'
    color = 'black'
    sizes = ['Large']
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'brand': brand,
            'color': color,
            'sizes': sizes
        },
        properties_to_be_removed=['description', 'title'])
    expected_title = f'{sizes[0]} {brand} {color}'
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']

    self.assertEqual(expected_title, product.get('title'))
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_title_not_created_from_description_if_title_already_exists(self):
    brand = 'Nike'
    color = 'black'
    description = 'Product that is missing a title but has a description'
    sizes = ['Large']
    original_title = 'Product Title'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'brand': brand,
            'color': color,
            'description': description,
            'title': original_title,
            'sizes': sizes
        })
    expected_title = f'{original_title}… {sizes[0]} {brand} {color}'
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, _ = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']

    self.assertEqual(expected_title, product.get('title'))

  def test_title_over_150_chars_does_not_append_attributes(self):
    title = ('[OPTI] Titlelength:Over150charsaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
             'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
             'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa bbbbb')
    description = (
        'NIKE  バスケットボール メンズソックス ジョーダン '
        'アルティメット フライト 2.0 グリップ クルー '
        'ソックス SX5851-010')
    color = 'レッド'
    sizes = ['L']
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'color': color,
            'description': description,
            'title': title,
            'sizes': sizes
        })
    expected_title = ('[OPTI] Titlelength:Over150charsaaaaaaaaaaaaaaaaaaaaaaaaa'
                      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
                      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)
    optimized_data, _ = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']

    self.assertEqual(expected_title, product['title'])


class TitleOptimizerBrandTest(parameterized.TestCase):

  def setUp(self):
    super(TitleOptimizerBrandTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = title_optimizer.TitleOptimizer()
    self.fields_to_append = ['gender', 'color', 'sizes', 'brand']

  def test_process_appends_brand_when_brand_valid(self):
    original_title = 'dummy title'
    brand_to_append = 'Cool Company'
    self.fields_to_append.remove('brand')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'brand': brand_to_append,
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertIn(brand_to_append, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_does_not_append_brand_when_brand_empty(self):
    original_title = 'dummy title'
    self.fields_to_append.remove('brand')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'brand': '',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_append_brand_when_brand_does_not_exist(self):
    original_title = 'dummy title'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'title': original_title},
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_append_brand_when_brand_over_70_chars(self):
    original_title = 'dummy title'
    brand_over_70_chars = 'a' * (attribute_miner._MAX_BRAND_LENGTH * 2)
    self.fields_to_append.remove('brand')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'brand': brand_over_70_chars,
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_append_brand_when_brand_in_blocklist(self):
    original_title = 'dummy title'
    blocklisted_brand = 'null'
    self.fields_to_append.remove('brand')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'brand': blocklisted_brand,
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_append_brand_when_brand_already_in_title(self):
    brand_to_append = 'Cool Company'
    original_title = f'dummy title {brand_to_append}'
    self.fields_to_append.remove('brand')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'brand': brand_to_append,
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    self.assertIn(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_appends_brand_when_blocklist_empty(self):
    original_title = 'dummy title'
    brand_to_append = 'Cool Company'
    self.fields_to_append.remove('brand')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'brand': brand_to_append,
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    with mock.patch(
        'builtins.open',
        mock.mock_open(read_data='')), mock.patch('json.load'), mock.patch(
            'util.color_miner.ColorMiner') as mocked_color_miner, mock.patch(
                'util.size_miner.SizeMiner') as mocked_size_miner:
      mocked_color_miner.return_value.mine_color.return_value = None, None
      mocked_size_miner.return_value.mine_size.return_value = None
      mocked_size_miner.return_value.is_size_in_attribute = False
      optimized_data, optimization_result = optimizer.process(
          original_data, 'test')

      product = optimized_data['entries'][0]['product']
      self.assertIn(brand_to_append, product['title'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)


@mock.patch('util.color_miner._CONFIG_FILE_PATH',
            '../config/color_optimizer_config_{}_test.json')
class TitleOptimizerColorTest(parameterized.TestCase):

  def setUp(self):
    super(TitleOptimizerColorTest, self).setUp()
    self.optimizer = title_optimizer.TitleOptimizer()
    self.fields_to_append = ['gender', 'color', 'sizes', 'brand']

  def test_process_appends_color_when_the_field_has_value(self):
    original_title = 'dummy title'
    color_to_append = 'Black'
    self.fields_to_append.remove('color')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'color': color_to_append,
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'en')

    product = optimized_data['entries'][0]['product']

    self.assertIn(color_to_append, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  @parameterized.named_parameters([
      {
          'testcase_name': 'one color',
          'colors': ['レッド']
      },
      {
          'testcase_name': 'two colors',
          'colors': ['レッド', 'オレンジ']
      },
      {
          'testcase_name': 'three colors',
          'colors': ['レッド', 'オレンジ', 'グリーン']
      },
      {
          'testcase_name': 'four colors',
          'colors': ['レッド', 'オレンジ', 'グリーン', 'ブルー']
      },
  ])
  def test_process_inserts_at_most_three_colors_field_when_color_is_mined_in_title(
      self, colors):
    original_title = f'dummy title {"・".join(colors)}'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'googleProductCategory': 'ファッション・アクセサリー',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, _ = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']

    self.assertEqual('/'.join(colors[:constants.MAX_COLOR_COUNT]),
                     product.get('color'))

  @parameterized.named_parameters([
      {
          'testcase_name': 'one color',
          'colors': ['レッド']
      },
      {
          'testcase_name': 'two colors',
          'colors': ['レッド', 'オレンジ']
      },
      {
          'testcase_name': 'three colors',
          'colors': ['レッド', 'オレンジ', 'グリーン']
      },
      {
          'testcase_name': 'four colors',
          'colors': ['レッド', 'オレンジ', 'グリーン', 'ブルー']
      },
  ])
  def test_process_appends_at_most_three_colors_to_title_when_color_is_mined_in_description(
      self, colors):
    original_description = f'dummy description {"・".join(colors)}'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'description': original_description,
            'googleProductCategory': 'ファッション・アクセサリー',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']

    self.assertIn(' '.join(colors[:constants.MAX_COLOR_COUNT]),
                  product['title'])
    self.assertEqual('/'.join(colors[:constants.MAX_COLOR_COUNT]),
                     product.get('color'))
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_not_appends_duplicate_colors_to_title(self):
    original_title = 'dummy title レッド'
    self.fields_to_append.remove('color')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title レッド',
            'color': 'レッド',
            'googleProductCategory': 'ファッション・アクセサリー',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product.get('title'))
    self.assertEqual(0, optimization_result.num_of_products_optimized)


class TitleOptimizerGenderTest(parameterized.TestCase):

  def setUp(self):
    super(TitleOptimizerGenderTest, self).setUp()
    self.optimizer = title_optimizer.TitleOptimizer()
    self.fields_to_append = ['gender', 'color', 'sizes', 'brand']

  def test_process_appends_womens_to_title_from_female_gender(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'gender': 'female'
        },
        properties_to_be_removed=['color', 'sizes', 'brand'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Women\'s', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_mens_to_title_from_male_gender(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'gender': 'male',
            'googleProductCategory': 'Apparel & Accessories > Shoes'
        },
        properties_to_be_removed=['color', 'sizes', 'brand'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Men\'s', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_womens_to_title_from_female_product_type(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Women\'s', 'Shoes']
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Women\'s', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_unisex_to_title_from_explicit_description_terms(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'description': 'unisex shoes',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Unisex', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_unisex_to_title_from_multiple_description_terms(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'description': 'Men\'s and Women\'s shoes',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Unisex', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_mens_to_title_from_product_lowercase_description(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'description': 'men\'s shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Men\'s', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_womens_to_title_from_product_lowercase_description(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'description': 'women\'s shoes',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Women\'s', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_replace_the_end_of_title_with_gender_when_length_exceeds_max_after_desc_appended(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'aaaaa...',
            'description': 'a' * title_optimizer._MAX_TITLE_LENGTH,
            'gender': 'male',
            'googleProductCategory': 'Apparel & Accessories > Shoes'
        },
        properties_to_be_removed=['color', 'sizes', 'brand'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Men\'s', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_not_append_gender_when_gender_could_not_be_mined(self):
    original_title = 'dummy title'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'gender': '',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=['color', 'sizes', 'brand'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_not_append_gender_when_gender_value_is_in_title(self):
    original_title = 'dummy men\'s title'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'gender': 'male',
            'googleProductCategory': 'Apparel & Accessories > Shoes'
        },
        properties_to_be_removed=['color', 'sizes', 'brand'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_inserts_mined_gender_field_when_gender_could_be_mined(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'description': 'men\'s shoes',
            'gender': '',
            'googleProductCategory': 'Apparel & Accessories > Shoes'
        },
        properties_to_be_removed=['color', 'sizes'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual('male', product['gender'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_girls_to_title_from_female_baby_gender(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'dummy title',
            'gender':
                'female',
            'googleProductCategory':
                'Apparel & Accessories > Clothing > Baby & Toddler Clothing'
        },
        properties_to_be_removed=['color', 'sizes', 'brand'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn('Girl\'s', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_inserts_baby_gender_when_gender_could_be_mined(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'dummy title',
            'description':
                'boy\'s shoes',
            'gender':
                '',
            'googleProductCategory':
                'Apparel & Accessories > Clothing > Baby & Toddler Clothing'
        },
        properties_to_be_removed=['color', 'sizes'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual('male', product['gender'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_inserts_unisex_gender_for_baby_category(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'dummy title',
            'description':
                'boy\'s or girl\'s shoes',
            'gender':
                '',
            'googleProductCategory':
                'Apparel & Accessories > Clothing > Baby & Toddler Clothing'
        },
        properties_to_be_removed=['color', 'sizes'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual('unisex', product['gender'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_not_insert_gender_when_gender_could_not_be_mined(self):
    original_title = 'dummy title'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'gender': '',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=['color', 'sizes', 'brand'])

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual('', product['gender'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_doesnt_add_gender_to_title_when_category_is_not_target(self):
    original_title = 'dummy title'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                original_title,
            'description':
                'Men\'s cars',
            'gender':
                'male',
            'googleProductCategory':
                'Vehicles & Parts > Vehicle Parts & Accessories',
            'productTypes': ['Vehicles & Parts', 'Men\'s Cars']
        },
        properties_to_be_removed=['color', 'sizes', 'brand'])

    optimized_data, optimization_result = self.optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_title, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)


@mock.patch('util.color_miner._CONFIG_FILE_PATH',
            '../config/color_optimizer_config_{}_test.json')
class TitleOptimizerSizeTest(parameterized.TestCase):

  def setUp(self):
    super(TitleOptimizerSizeTest, self).setUp()
    self.optimizer = title_optimizer.TitleOptimizer()
    self.fields_to_append = ['gender', 'color', 'sizes', 'brand']

  def test_process_appends_sizes_when_the_field_has_value(self):
    original_title = 'dummy title'
    self.fields_to_append.remove('sizes')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': original_title,
            'sizes': ['Large']
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.COUNTRY_CODE_US).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')

    product = optimized_data['entries'][0]['product']
    expected_title = f'{original_title}… Large'
    self.assertIn(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_clothing_sizes_mining_from_description(self):
    size_term = 'L'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'Tシャツ',
            'description':
                f'{size_term}サイズ',
            'googleProductCategory':
                'ファッション・アクセサリー > 衣料品',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']
    self.assertIn(size_term, product['title'])
    self.assertEqual([size_term], product.get('sizes'))
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_appends_sizes_to_title_even_when_the_same_letter_is_included_in_other_words(
      self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'ORIGINAL BRAND Tシャツ',
            'description':
                'Tシャツ Lサイズ',
            'googleProductCategory':
                'ファッション・アクセサリー > 衣料品',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']
    self.assertIn('ORIGINAL BRAND Tシャツ… L', product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_does_not_mine_sizes_when_size_term_is_not_in_attributes(
      self):
    original_title = 'ORIGINAL BRAND Tシャツ'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                original_title,
            'description':
                'ORIGINAL BRAND Tシャツ',
            'googleProductCategory':
                'ファッション・アクセサリー > 衣料品',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']
    self.assertIn(original_title, product['title'])
    self.assertIsNone(product.get('sizes'))
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_appends_shoe_sizes_mining_from_description(self):
    size_term = '27.5'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'スニーカー',
            'description':
                f'{size_term}cm',
            'googleProductCategory':
                'ファッション・アクセサリー > 靴',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']
    self.assertIn(size_term, product['title'])
    self.assertEqual([size_term], product.get('sizes'))
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_does_not_append_sizes_when_size_is_already_in_title(self):
    size_term = 'L'
    self.fields_to_append.remove('sizes')
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title':
                'TシャツM',
            'sizes': [size_term],
            'googleProductCategory':
                'ファッション・アクセサリー > 衣料品',
        },
        properties_to_be_removed=self.fields_to_append)
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(original_data, 'ja')

    product = optimized_data['entries'][0]['product']
    self.assertNotIn(size_term, product['title'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)


class TitleOptimizerRemovingTextTest(parameterized.TestCase):

  def setUp(self):
    super(TitleOptimizerRemovingTextTest, self).setUp()
    app_util.setup_test_app()
    self.optimizer = title_optimizer.TitleOptimizer()
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
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)

    product = optimized_data['entries'][0]['product']
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

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
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)

    product = optimized_data['entries'][0]['product']
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

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
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_JA,
        constants.COUNTRY_CODE_JP).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = title_optimizer.TitleOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, constants.LANGUAGE_CODE_JA)

    product = optimized_data['entries'][0]['product']
    self.assertEqual(expected_title, product['title'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)
