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

"""A module that mines attributes from products.

This is the top level attribute miner and can be used to call lower level miners
such as color_miner.
"""

import collections
import logging
from typing import Any, Dict, Optional, OrderedDict, Set
from flask import current_app

import original_types
from util import color_miner
from util import gender_miner
from util import size_miner

_MAX_BRAND_LENGTH: int = 70


class AttributeMiner(object):
  """A class that mines attributes from products."""

  _brand_blocklist: Set[str] = ()
  _color_miner: Optional[color_miner.ColorMiner] = None
  _gender_miner: Optional[gender_miner.GenderMiner] = None
  _size_miner: Optional[size_miner.SizeMiner] = None

  def __init__(self, language: str, country: str) -> None:
    """Initializes AttributeMiner.

    Args:
      language: The configured language code.
      country: The configured country code.
    """
    super(AttributeMiner, self).__init__()
    brand_blocklist_config = current_app.config.get('CONFIGS', {}).get(
        'brand_blocklist', {})
    self._brand_blocklist = set(
        [brand.lower() for brand in brand_blocklist_config])

    self._color_miner = color_miner.ColorMiner(language)
    self._gender_miner = gender_miner.GenderMiner(language)
    self._size_miner = size_miner.SizeMiner(language, country)

  def mine_and_insert_attributes_for_batch(
      self, product_batch: Dict[str, Any]) -> original_types.MinedAttributes:
    """Mines attributes (specified below) and inserts them in to product fields.

    The fields to be appended are:
    - gender
    - color
    - sizes
    - brand

    Args:
      product_batch: A batch of product data.

    Returns:
      A list of mined attributes mapped to product ids in the batch.
    """
    mining_results_for_products = {}

    for entry in product_batch['entries']:
      product = entry['product']
      mined_attributes = self._mine_and_insert_attributes_for_product(product)
      product_id = product['offerId']
      mining_results_for_products[product_id] = mined_attributes

    return mining_results_for_products

  def _mine_and_insert_attributes_for_product(
      self, product: Dict[str, Any]) -> OrderedDict[str, Any]:
    """Mines attributes (specified below) and inserts them into product fields.

    The fields to be appended are:
    - gender
    - color
    - sizes
    - brand

    Args:
      product: A dictionary containing product data.

    Returns:
      A list of the attributes mined from this product.
    """
    mined_attributes = collections.OrderedDict()

    gender = self._gender_miner.mine_gender(product)
    if gender:
      google_gender_field = gender[0]
      _insert_value_in_field(product, 'gender', google_gender_field)

      gender_replacement_field = gender[1]
      mined_attributes['gender'] = gender_replacement_field

    size = self._size_miner.mine_size(product)
    if size:
      _insert_value_in_field(product, 'sizes', [size])
      mined_attributes['sizes'] = [size]

    brand = product.get('brand')
    if self._brand_is_valid(brand):
      mined_attributes['brand'] = brand

    standard_colors, unique_colors = self._color_miner.mine_color(product)
    if standard_colors:
      mined_attributes['color'] = standard_colors

    if unique_colors:
      _insert_value_in_field(product, 'color', '/'.join(unique_colors))

    return mined_attributes

  def _brand_is_valid(self, brand: str) -> bool:
    """Checks if the given brand is valid or not.

    A valid brand is one which is:
      1. Not empty
      2. Less than or equal to the max possible length for brand
      3. Not contained in the brand blocklist

    Args:
      brand: The brand that will be checked for validity.

    Returns:
      True if the brand is valid, False otherwise.
    """
    return brand and len(brand) <= _MAX_BRAND_LENGTH and brand.lower(
    ) not in self._brand_blocklist


def _insert_value_in_field(product: Dict[str, Any], field: str,
                           value: Any) -> None:
  """Inserts the value into the product target field only if it doesn't exist.

  Args:
    product: A dictionary containing product data.
    field: The target field name.
    value: The field value.
  """
  if not product.get(field):
    product[field] = value
    logging.info('Modified item %s: Inserting mined %s in field: %s',
                 product['offerId'], field, value)
