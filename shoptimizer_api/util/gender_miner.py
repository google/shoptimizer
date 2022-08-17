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

"""A module that mines gender from product data.

This module mines gender from the product data using the gender
and category config files.

References
- Google Merchant Center Help Center:
https://support.google.com/merchants/answer/6324479?hl=en
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from util import config_parser
from util import gpc_id_to_string_converter

_GENDER_OPTIMIZER_CONFIG_FILE_NAME: str = 'gender_optimizer_config_{}'
_GENDER_OPTIMIZER_CONFIG_OVERRIDE_KEY: str = 'gender_optimizer_config_override'
_GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME: str = 'gpc_string_to_id_mapping_{}'

_ADULT: str = 'adult'
_BABY: str = 'baby'
_FEMALE: str = 'female'
_MALE: str = 'male'
_UNISEX: str = 'unisex'
_VALID_GENDER_VALUES: List[str] = [_FEMALE, _MALE, _UNISEX]


class GenderMiner(object):
  """A class that mines color from product data."""

  _gender_config: Optional[Dict[str, Any]] = None
  _gpc_id_to_string_converter: Optional[
      gpc_id_to_string_converter.GPCConverter] = None

  def __init__(self, language: str) -> None:
    """Initializes GenderMiner.

    Args:
      language: The configured language code.
    """
    super(GenderMiner, self).__init__()

    self._gender_config = config_parser.get_config_contents(
        _GENDER_OPTIMIZER_CONFIG_OVERRIDE_KEY,
        _GENDER_OPTIMIZER_CONFIG_FILE_NAME.format(language))

    self._gpc_id_to_string_converter = gpc_id_to_string_converter.GPCConverter(
        _GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME.format(language))

  def mine_gender(self, product: Dict[str, Any]) -> Optional[Tuple[str, str]]:
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

    gpc_string = self._gpc_id_to_string_converter.convert_gpc_id_to_string(
        google_product_category)

    age_demographic = self._get_age_demographic_if_category_is_gendered(
        gpc_string)

    # Only try mining the gender if the product's category was found
    # in either the baby/adult configurations. age_demographic will be unset
    # if the category was not a target gendered category.
    if age_demographic:
      title_replacement_config_key = age_demographic + '_title_replacement'

      mined_gender = self._validate_gender_field(
          gender_value) or self._get_gender_from_product_types(
              age_demographic,
              product_types) or self._get_gender_from_description(
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

    baby_categories = self._gender_config.get(_BABY + '_product_categories', [])
    if any(category in baby_categories for category in product_categories):
      return _BABY

    adult_categories = (
        self._gender_config.get(_ADULT + '_product_categories', []))
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
      A string containing the gender of the product, or None if the
      gender could not be found.
    """
    if isinstance(product_types, list) and product_types:
      concat_product_types = ' '.join(product_types)
      search_terms_config_key = age_demographic + '_search_terms'
      for gender in [_FEMALE, _MALE, _UNISEX]:
        search_terms = self._gender_config.get(gender,
                                               {}).get(search_terms_config_key,
                                                       [])
        if self._text_contains_terms(concat_product_types, search_terms):
          return gender
    return None

  def _get_gender_from_description(self, age_demographic: str,
                                   description: str) -> str:
    """Extracts the gender from the provided description field.

    Args:
      age_demographic: A string representing either "adult" or "baby".
      description: A string representing the product description.

    Returns:
      A string containing the gender of the product, or None if the
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

    if self._text_contains_terms(description, unisex_search_terms):
      return _UNISEX

    female_found = False
    male_found = False

    if self._text_contains_terms(description, female_search_terms):
      female_found = True
      # Removes the female terms in case the male ones are a substring.
      description = self._remove_terms_from_description(description,
                                                        female_search_terms)

    if self._text_contains_terms(description, male_search_terms):
      male_found = True

    if female_found and male_found:
      return _UNISEX
    if female_found:
      return _FEMALE
    if male_found:
      return _MALE
    return None

  def _validate_gender_field(self, gender_field: str) -> str:
    """Returns the provided gender field if it was valid gender value.

    Args:
      gender_field: A string representing the gender field value.

    Returns:
      A string containing the gender of the product, or an empty string if the
      gender could not be found.
    """
    if gender_field in _VALID_GENDER_VALUES:
      return gender_field
    return ''

  def _remove_terms_from_description(self, description: str,
                                     search_terms: List[str]) -> str:
    """Removes the provided terms from the provided description string.

    Args:
      description: A string representing the product description.
      search_terms: A list of localized terms to remove from the description.

    Returns:
      A string containing the modified description string with the provided
      terms
      removed if they were found.
    """
    for keyword in search_terms:
      description = description.lower().replace(keyword.lower(), '')
    return description

  def _text_contains_terms(self, field_text: str,
                           search_terms: List[str]) -> bool:
    """Checks if any provided search term was found in the provided text.

    Args:
      field_text: A string representing a product field value.
      search_terms: A list of localized terms to find in the field_text string.

    Returns:
      True if any terms were found in the field_text string, otherwise False.
    """
    return any(
        keyword.lower() in field_text.lower() for keyword in search_terms)
