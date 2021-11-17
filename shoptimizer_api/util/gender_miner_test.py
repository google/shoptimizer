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

"""Unit tests for gender_miner.py."""

import unittest
import unittest.mock as mock

import constants
from test_data import requests_bodies
from util import app_util
from util import gender_miner


@mock.patch('util.gender_miner._GENDER_OPTIMIZER_CONFIG_FILE_NAME',
            'gender_optimizer_config_{}_test')
@mock.patch('util.gender_miner._GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME',
            'gpc_string_to_id_mapping_{}_test')
class GenderMinerTest(unittest.TestCase):

  def setUp(self):
    super(GenderMinerTest, self).setUp()
    app_util.setup_test_app()

  def test_mine_gender_mines_womens_from_female_gender(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'gender': 'female'
        })

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn("Women's", mined_attributes[1])

  def test_mine_gender_mines_mens_from_male_gender(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'gender': 'male',
            'googleProductCategory': 'Apparel & Accessories > Shoes'
        })

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn("Men's", mined_attributes[1])

  def test_mine_gender_mines_womens_from_female_product_type(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Women\'s', 'Shoes']
        },
        properties_to_be_removed=['gender'])

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn("Women's", mined_attributes[1])

  def test_mine_gender_mines_womens_using_gpc_number(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'googleProductCategory': 187,
            'productTypes': ['Apparel & Accessories', 'Women\'s', 'Shoes']
        },
        properties_to_be_removed=['gender'])

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn("Women's", mined_attributes[1])

  def test_mine_gender_mines_unisex_from_explicit_description_terms(
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

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn('Unisex', mined_attributes[1])

  def test_mine_gender_mines_unisex_from_multiple_description_terms(
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

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn('Unisex', mined_attributes[1])

  def test_mine_gender_mines_mens_from_product_lowercase_description(
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

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn("Men's", mined_attributes[1])

  def test_mine_gender_mines_womens_from_product_lowercase_description(
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

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn("Women's", mined_attributes[1])

  def test_mine_gender_not_contains_gender_when_gender_could_not_be_mined(
      self):
    product_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'offerId': 'product-1',
            'title': 'dummy title',
            'gender': '',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': ['Apparel & Accessories', 'Shoes']
        })

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIsNone(mined_attributes)

  def test_mine_gender_mines_girls_from_female_baby_gender(
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

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIn("Girl's", mined_attributes[1])

  def test_mine_gender_mines_baby_gender(self):
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

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertEqual('male', mined_attributes[0])

  def test_mine_gender_mines_unisex_gender_for_baby_category(
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

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertEqual('unisex', mined_attributes[0])

  def test_mine_gender_doesnt_mine_gender_when_category_is_not_target(
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

    miner = gender_miner.GenderMiner(constants.LANGUAGE_CODE_EN)

    mined_attributes = miner.mine_gender(product_data['entries'][0]['product'])

    self.assertIsNone(mined_attributes)
