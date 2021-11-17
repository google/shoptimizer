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

"""Unit tests for description_optimizer.py."""

from absl.testing import parameterized

import constants
from optimizers_builtin import description_optimizer
from test_data import requests_bodies
from util import attribute_miner
from util import app_util


class DescriptionOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(DescriptionOptimizerTest, self).setUp()
    app_util.setup_test_app()

  def test_brand_appended_to_description(self):
    original_description = 'Dummy Description.'
    brand_to_append = 'Cool Company'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': original_description,
            'brand': brand_to_append
        })
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.DEFAULT_COUNTRY).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = description_optimizer.DescriptionOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn(brand_to_append, product['description'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_color_appended_to_description(self):
    original_description = 'Dummy Description.'
    color_to_append = 'Black'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': original_description,
            'color': color_to_append
        })
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.DEFAULT_COUNTRY).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = description_optimizer.DescriptionOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn(color_to_append, product['description'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_gender_appended_to_description(self):
    female_product_type = ['Apparel & Accessories', "Women's", 'Shoes']
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'title': 'dummy title',
            'googleProductCategory': 'Apparel & Accessories > Shoes',
            'productTypes': female_product_type
        },
        properties_to_be_removed=['gender'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.DEFAULT_COUNTRY).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = description_optimizer.DescriptionOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn("Women's", product['description'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_sizes_appended_to_description(self):
    original_description = 'Dummy Description.'
    sizes_to_append = ['Large']
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': original_description,
            'sizes': sizes_to_append
        })
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.DEFAULT_COUNTRY).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = description_optimizer.DescriptionOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn(sizes_to_append[0], product['description'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_multiple_fields_appended_to_description(self):
    original_description = 'Dummy Description.'
    brand_to_append = 'Cool Company'
    color_to_append = 'Black'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': original_description,
            'brand': brand_to_append,
            'color': color_to_append
        })
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.DEFAULT_COUNTRY).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = description_optimizer.DescriptionOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertIn(brand_to_append, product['description'])
    self.assertIn(color_to_append, product['description'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_attribute_not_appended_to_description_if_it_already_exists_in_description(
      self):
    original_description = 'Dummy Description. Cool Company.'
    brand_to_append = 'Cool Company'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': original_description,
            'brand': brand_to_append
        },
        properties_to_be_removed=['color', 'sizes', 'gender'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.DEFAULT_COUNTRY).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = description_optimizer.DescriptionOptimizer(mined_attrs)

    _, optimization_result = optimizer.process(original_data, 'test')

    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_attribute_not_appended_to_description_it_not_enough_space(self):
    original_description = 'a' * description_optimizer._MAX_DESCRIPTION_LENGTH
    brand_to_append = 'Cool Company'
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'description': original_description,
            'brand': brand_to_append
        })
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.DEFAULT_COUNTRY).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = description_optimizer.DescriptionOptimizer(mined_attrs)

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(original_description, product['description'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_description_created_if_it_does_not_exist(self):
    brand_to_append = 'Cool Company'
    color_to_append = 'Black'
    sizes_to_append = ['Large']
    gender = 'male'
    gender_title_replacement = "Men's"
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'brand': brand_to_append,
            'color': color_to_append,
            'sizes': sizes_to_append,
            'gender': gender
        },
        properties_to_be_removed=['description'])
    mined_attrs = attribute_miner.AttributeMiner(
        constants.LANGUAGE_CODE_EN,
        constants.DEFAULT_COUNTRY).mine_and_insert_attributes_for_batch(
            original_data)
    optimizer = description_optimizer.DescriptionOptimizer(mined_attrs)
    expected_description = (
        f'{gender_title_replacement} {sizes_to_append[0]} {brand_to_append} '
        f'{color_to_append}')

    optimized_data, optimization_result = optimizer.process(
        original_data, 'test')
    product = optimized_data['entries'][0]['product']

    self.assertEqual(expected_description, product['description'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)
