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

"""Unit tests for attribute_miner.py."""

import unittest
import unittest.mock as mock

import constants
from test_data import requests_bodies
from util import app_util
from util import attribute_miner


@mock.patch('util.gender_miner._GENDER_OPTIMIZER_CONFIG_FILE_NAME',
            'gender_optimizer_config_{}_test')
@mock.patch('util.gender_miner._GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME',
            'gpc_string_to_id_mapping_{}_test')
class AttributeMinerTest(unittest.TestCase):

  def setUp(self):
    super(AttributeMinerTest, self).setUp()
    app_util.setup_test_app()

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_womens_from_female_gender(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'gender': 'female'
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn("Women's", mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_mens_from_male_gender(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'gender': 'male',
            'googleProductCategory': 'Apparel & Accessories > Shoes'
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn("Men's", mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_womens_from_female_product_type(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Women\'s', 'Shoes']
        },
        properties_to_be_removed=['gender'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn("Women's", mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'False'
          }
      })
  def test_mine_and_insert_attributes_for_batch_doesnt_overwrite_gender_attribute_if_header_is_false(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Women\'s', 'Shoes'],
            'gender': 'male'
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertEqual('male', product['gender'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_womens_using_gpc_number(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 187,
            'productTypes': ['Apparel & Accessories', 'Women\'s', 'Shoes']
        },
        properties_to_be_removed=['gender'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn("Women's", mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_unisex_from_explicit_description_terms(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'description': 'unisex shoes',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=['gender'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn('Unisex', mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_unisex_from_multiple_description_terms(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'description': 'Men\'s and Women\'s shoes',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=['gender'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn('Unisex', mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_mens_from_product_lowercase_description(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'description': 'men\'s shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=['gender'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn("Men's", mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_womens_from_product_lowercase_description(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'description': 'women\'s shoes',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        },
        properties_to_be_removed=['gender'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn("Women's", mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_does_not_contain_gender_when_gender_could_not_be_mined(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'gender': '',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertNotIn('Unisex', mined_attributes['product-1'])
    self.assertNotIn("Men's", mined_attributes['product-1'])
    self.assertNotIn("Women's", mined_attributes['product-1'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_girls_from_female_baby_gender(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId':
                'product-1',
            'title':
                'dummy title',
            'gender':
                'female',
            'googleProductCategory':
                'Apparel & Accessories > Clothing > Baby & Toddler Clothing'
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn("Girl's", mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_baby_gender(self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId':
                'product-1',
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
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertEqual('male', product['gender'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_unisex_gender_for_baby_category(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId':
                'product-1',
            'title':
                'dummy title',
            'description':
                'boy\'s or girl\'s shoes',
            'gender':
                '',
            'googleProductCategory':
                'Apparel & Accessories > Clothing > Baby & Toddler Clothing'
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertEqual('unisex', product['gender'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_doesnt_mine_gender_when_category_is_not_target(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId':
                'product-1',
            'title':
                'dummy title',
            'description':
                'Men\'s cars',
            'gender':
                'male',
            'googleProductCategory':
                'Vehicles & Parts > Vehicle Parts & Accessories',
            'productTypes': ['Vehicles & Parts', 'Men\'s Cars']
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertNotIn('Unisex', mined_attributes['product-1'])
    self.assertNotIn("Men's", mined_attributes['product-1'])
    self.assertNotIn("Women's", mined_attributes['product-1'])

  @mock.patch.dict('flask.current_app.config',
                   {'MINING_OPTIONS': {
                       'gender_mining_on': 'False',
                   }})
  def test_mine_and_insert_attributes_for_batch_doesnt_mine_gender_when_header_set_to_false(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'gender': 'female'
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIsNone(mined_attributes['product-1'].get('gender'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'color_mining_on': 'True',
              'color_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_for_batch_mines_color(self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'タイトルレッド・オレンジ'
        },
        properties_to_be_removed=['color'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_JA,
                                           constants.COUNTRY_CODE_JP)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn('レッド', mined_attributes['product-1'].get('color'))
    self.assertIn('オレンジ', mined_attributes['product-1'].get('color'))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'color_mining_on': 'True',
              'color_mining_overwrite': 'False'
          }
      })
  def test_mine_and_insert_attributes_for_batch_doesnt_overwrite_color_if_header_is_false(
      self):
    product_data = requests_bodies.build_request_body(properties_to_be_updated={
        'offerId': 'product-1',
        'title': 'タイトルレッド・オレンジ',
        'color': 'blue'
    })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_JA,
                                           constants.COUNTRY_CODE_JP)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertEqual('blue', product['color'])

  @mock.patch.dict('flask.current_app.config',
                   {'MINING_OPTIONS': {
                       'color_mining_on': 'False',
                   }})
  def test_mine_and_insert_attributes_for_batch_doesnt_mine_color_when_header_is_false(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'タイトルレッド・オレンジ'
        },
        properties_to_be_removed=['color'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_JA,
                                           constants.COUNTRY_CODE_JP)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIsNone(mined_attributes['product-1'].get('color'))

  @mock.patch.dict('flask.current_app.config', {
      'MINING_OPTIONS': {
          'size_mining_on': 'True',
          'size_mining_overwrite': 'True'
      }
  })
  def test_mine_and_insert_attributes_for_batch_mines_and_inserts_sizes(self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'description': 'TシャツL',
        },
        properties_to_be_removed=['sizes'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_JA,
                                           constants.COUNTRY_CODE_JP)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertIn('L', product['sizes'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'size_mining_on': 'True',
              'size_mining_overwrite': 'False'
          }
      })
  def test_mine_and_insert_attributes_for_batch_doesnt_overwrite_sizes_if_header_is_false(
      self):
    product_data = requests_bodies.build_request_body(properties_to_be_updated={
        'offerId': 'product-1',
        'description': 'TシャツL',
        'sizes': ['M']
    })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_JA,
                                           constants.COUNTRY_CODE_JP)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertEqual(['M'], product['sizes'])

  @mock.patch.dict('flask.current_app.config',
                   {'MINING_OPTIONS': {
                       'size_mining_on': 'False'
                   }})
  def test_mine_and_insert_attributes_for_batch_doesnt_mine_size_when_header_is_false(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'description': 'TシャツL',
        },
        properties_to_be_removed=['sizes'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_JA,
                                           constants.COUNTRY_CODE_JP)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIsNone(mined_attributes['product-1'].get('sizes'))

  @mock.patch.dict('flask.current_app.config',
                   {'MINING_OPTIONS': {
                       'brand_mining_on': 'True',
                   }})
  def test_mine_and_insert_attributes_for_batch_mines_brand(self):
    product_data = requests_bodies.build_request_body(properties_to_be_updated={
        'offerId': 'product-1',
        'brand': 'Gucci'
    })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIn('Gucci', mined_attributes['product-1'].get('brand'))

  @mock.patch.dict('flask.current_app.config',
                   {'MINING_OPTIONS': {
                       'brand_mining_on': 'False',
                   }})
  def test_mine_and_insert_attributes_for_batch_doesnt_mine_brand_if_header_is_false(
      self):
    product_data = requests_bodies.build_request_body(properties_to_be_updated={
        'offerId': 'product-1',
        'brand': 'Gucci'
    })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertIsNone(mined_attributes['product-1'].get('brand'))

  @mock.patch.dict('flask.current_app.config',
                   {'MINING_OPTIONS': {
                       'brand_mining_on': 'True',
                   }})
  def test_mine_and_insert_attributes_for_batch_does_not_mine_brand_if_brand_too_long(
      self):
    invalid_brand = 'brandthatistoolong' * attribute_miner._MAX_BRAND_LENGTH
    product_data = requests_bodies.build_request_body(properties_to_be_updated={
        'offerId': 'product-1',
        'brand': invalid_brand
    })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertNotIn(invalid_brand, mined_attributes['product-1'])

  @mock.patch.dict('flask.current_app.config',
                   {'MINING_OPTIONS': {
                       'brand_mining_on': 'True',
                   }})
  def test_process_does_not_append_brand_when_brand_in_blocklist(self):
    blocklisted_brand = 'null'
    product_data = requests_bodies.build_request_body(properties_to_be_updated={
        'offerId': 'product-1',
        'brand': blocklisted_brand,
    })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertNotIn(blocklisted_brand, mined_attributes['product-1'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_inserts_gender_into_gender_field(self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Women\'s', 'Shoes']
        },
        properties_to_be_removed=['gender'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertEqual('female', product['gender'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'gender_mining_on': 'True',
              'gender_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_does_not_insert_gender_into_gender_field_if_gender_field_not_empty(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Women\'s', 'Shoes'],
            'gender': 'unisex'
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertEqual('unisex', product['gender'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'color_mining_on': 'True',
              'color_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_inserts_colors_into_color_field(self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'タイトルレッド・オレンジ'
        },
        properties_to_be_removed=['color'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_JA,
                                           constants.COUNTRY_CODE_JP)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertIn('レッド/オレンジ', product['color'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'color_mining_on': 'True',
              'color_mining_overwrite': 'True'
          }
      })
  def test_mine_and_insert_attributes_does_not_inserts_colors_into_color_field_if_color_field_not_empty(
      self):
    product_data = requests_bodies.build_request_body(properties_to_be_updated={
        'offerId': 'product-1',
        'title': 'タイトルレッド・オレンジ',
        'color': 'Red'
    })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_JA,
                                           constants.COUNTRY_CODE_JP)

    _ = miner.mine_and_insert_attributes_for_batch(product_data)
    product = product_data['entries'][0]['product']

    self.assertIn('Red', product['color'])

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'brand_mining_on': 'True',
              'color_mining_on': 'True',
              'gender_mining_on': 'True',
              'size_mining_on': 'True'
          }
      })
  def test_mine_and_insert_attributes_returns_empty_list_for_product_when_no_attributes_mined(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={'offerId': 'product-1'},
        properties_to_be_removed=['brand', 'color', 'gender', 'sizes'])
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertEqual(0, len(mined_attributes['product-1']))

  @mock.patch.dict(
      'flask.current_app.config', {
          'MINING_OPTIONS': {
              'brand_mining_on': 'Error',
              'color_mining_on': 'Error',
              'gender_mining_on': 'Error',
              'size_mining_on': 'Error'
          }
      })
  def test_mine_and_insert_attributes_mines_nothing_when_option_is_invalid(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'タイトルレッド・オレンジ',
            'googleProductCategory': 'Apparel & Accessories',
            'description': 'TシャツL',
            'gender': 'female'
        })
    miner = attribute_miner.AttributeMiner(constants.LANGUAGE_CODE_EN,
                                           constants.DEFAULT_COUNTRY)

    mined_attributes = miner.mine_and_insert_attributes_for_batch(product_data)

    self.assertEqual(0, len(mined_attributes['product-1']))
