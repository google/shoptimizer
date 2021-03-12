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

"""A module that mines attributes from products.

This is the top level attribute miner and can be used to call lower level miners
such as color_miner.
"""

import collections
import logging
from typing import Any, Dict, List, Optional, OrderedDict, Set, Tuple
from flask import current_app

import original_types
from util import color_miner
from util import size_miner

_MAX_BRAND_LENGTH: int = 70

_ADULT: str = 'adult'
_BABY: str = 'baby'
_FEMALE: str = 'female'
_MALE: str = 'male'
_UNISEX: str = 'unisex'
_VALID_GENDER_VALUES: List[str] = [_FEMALE, _MALE, _UNISEX]


class AttributeMiner(object):
  """A class that mines attributes from products."""

  _brand_blocklist: Set[str] = ()
  _color_miner: Optional[color_miner.ColorMiner] = None
  _size_miner: Optional[size_miner.SizeMiner] = None
  _gender_config: Optional[Dict[str, Any]] = None

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
    self._gender_config = current_app.config.get('CONFIGS', {}).get(
        f'gender_optimizer_config_{language}', {})
    self._color_miner = color_miner.ColorMiner(language)
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
    """Mines attributes (specified below) and inserts them in to product fields.

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

    gender = self._mine_gender(product)
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

  def _mine_gender(self, product: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """Mines the gender from product fields.

    Args:
      product: A dictionary containing product data.

    Returns:
      A Tuple containing the gender of the product and the gender replacement
      term, or None if it was not able to be mined. This value is specified in
      the config file mapping in this repository
      (..config/gender_optimization_{language}.json). The reason for this is so
      that all optimized values have a consistent replacement, especially if
      there are multiple values found as in the unisex case.
    """
    if not self._gender_config:
      logging.warning(
          'Did not attempt to mine gender since gender config could not be '
          'loaded')
      return None

    gender_value = product.get('gender', '')
    google_product_category = product.get('googleProductCategory', '')
    product_types = product.get('productTypes', [])
    description = product.get('description', '')

    age_demographic = self._get_age_demographic_if_category_is_gendered(
        google_product_category)

    # Only try mining the gender if the product's category was found
    # in either the baby/adult configurations. age_demographic will be unset
    # if the category was not a target gendered category.
    if age_demographic:
      title_replacement_config_key = age_demographic + '_title_replacement'
      mined_gender = _get_gender_from_gender_field(gender_value)

      if not mined_gender:
        mined_gender = self._get_gender_from_product_types(
            age_demographic, product_types)

      if not mined_gender:
        mined_gender = self._get_gender_from_description(
            age_demographic, description)

      if mined_gender:
        title_replacement_value = self._gender_config.get(mined_gender, {}).get(
            title_replacement_config_key, None)
        return mined_gender, title_replacement_value
    return None

  def _get_age_demographic_if_category_is_gendered(
      self, google_product_category: str) -> Optional[str]:
    """Checks if the provided category was found in the config dict.

    Args:
      google_product_category: A string representing the product category.

    Returns:
      A string representing the age demographic if the product's category
      matched the gender config's list of categories, or an empty string if
      the product's category is not a target for gender mining.
    """
    product_categories = google_product_category.split(' > ')
    categories_config_key_adult = _ADULT + '_product_categories'
    categories_config_key_baby = _BABY + '_product_categories'

    baby_categories = self._gender_config.get(categories_config_key_baby, [])
    if any(category in baby_categories for category in product_categories):
      return _BABY

    adult_categories = self._gender_config.get(categories_config_key_adult, [])
    if any(category in adult_categories for category in product_categories):
      return _ADULT

    return None

  def _get_gender_from_product_types(self, age_demographic: str,
                                     product_types: List[str]) -> str:
    """Extracts the gender from the productTypes field.

    Args:
      age_demographic: A string representing either "adult" or "baby".
      product_types: A list of product type strings.

    Returns:
      A string containing the gender of the product, or an empty string if the
      gender could not be found.
    """
    if isinstance(product_types, list) and product_types:
      concat_product_types = ' '.join(product_types)
      search_terms_config_key = age_demographic + '_search_terms'
      for gender in [_FEMALE, _MALE, _UNISEX]:
        search_terms = self._gender_config.get(gender,
                                               {}).get(search_terms_config_key,
                                                       [])
        if _text_contains_terms(concat_product_types, search_terms):
          return gender
    return ''

  def _get_gender_from_description(self, age_demographic: str,
                                   description: str) -> str:
    """Extracts the gender from the provided description field.

    Args:
      age_demographic: A string representing either "adult" or "baby".
      description: A string representing the product description.

    Returns:
      A string containing the gender of the product, or an empty string if the
      gender could not be found.
    """
    search_terms_config_key = age_demographic + '_search_terms'
    female_search_terms = self._gender_config.get(_FEMALE, {}).get(
        search_terms_config_key, [])
    male_search_terms = self._gender_config.get(_MALE,
                                                {}).get(search_terms_config_key,
                                                        [])
    unisex_search_terms = self._gender_config.get(_UNISEX, {}).get(
        search_terms_config_key, [])

    if _text_contains_terms(description, unisex_search_terms):
      return _UNISEX

    female_found = False
    male_found = False

    if _text_contains_terms(description, female_search_terms):
      female_found = True
      # Removes the female terms in case the male ones are a substring.
      description = _remove_terms_from_description(description,
                                                   female_search_terms)

    if _text_contains_terms(description, male_search_terms):
      male_found = True

    if female_found and male_found:
      return _UNISEX
    if female_found:
      return _FEMALE
    if male_found:
      return _MALE
    return ''

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


def _get_gender_from_gender_field(gender_field: str) -> str:
  """Extracts the gender from the gender field if it was valid gender value.

  Args:
    gender_field: A string representing the gender field value.

  Returns:
    A string containing the gender of the product, or an empty string if the
    gender could not be found.
  """
  if gender_field in _VALID_GENDER_VALUES:
    return gender_field
  return ''


def _remove_terms_from_description(description: str,
                                   search_terms: List[str]) -> str:
  """Removes the provided terms from the provided description string.

  Args:
    description: A string representing the product description.
    search_terms: A list of localized terms to remove from the description.

  Returns:
    A string containing the modified description string with the provided terms
    removed if they were found.
  """
  for keyword in search_terms:
    description = description.lower().replace(keyword.lower(), '')
  return description


def _text_contains_terms(field_text: str, search_terms: List[str]) -> bool:
  """Checks if any of the provided search terms was found in the provided text.

  Args:
    field_text: A string representing a product field value.
    search_terms: A list of localized terms to find in the field_text string.

  Returns:
    True if any terms were found in the field_text string, otherwise False.
  """
  return any(keyword.lower() in field_text.lower() for keyword in search_terms)


def _insert_value_in_field(product: Dict[str, Any], field: str,
                           value: Any) -> None:
  """Inserts the value into the target field of the product.

  Args:
    product: A dictionary containing product data.
    field: The target field name.
    value: The field value.
  """
  if not product.get(field):
    product[field] = value
    logging.info('Modified item %s: Inserting mined %s in field: %s',
                 product['offerId'], field, value)
