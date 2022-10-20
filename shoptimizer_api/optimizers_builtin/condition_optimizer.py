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

"""A module for Shoptimizer API that fixes invalid condition values.

Reference: https://support.google.com/merchants/answer/6324469

If the condition field is specified as "new", but other fields in the
product imply that the condition is otherwise, this optimizer will reset
the condition value to "used".
"""
import logging
from typing import Any, Dict, List, Optional, Set

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import config_parser
from util import gpc_id_to_string_converter
from util import optimization_util

_CONDITION_OPTIMIZER_CONFIG_FILENAME = 'condition_optimizer_config_{}'
_CONDITION_OPTIMIZER_CONFIG_OVERRIDE_KEY = 'condition_optimizer_config_override'
_GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME: str = 'gpc_string_to_id_mapping_{}'
_NEW = 'new'
_USED = 'used'


class ConditionOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that fixes invalidly-set condition fields."""

  _OPTIMIZER_PARAMETER = 'condition-optimizer'
  _condition_config = None
  _gpc_id_to_string_converter: Optional[
      gpc_id_to_string_converter.GPCConverter] = None

  def _optimize(
      self, product_batch: Dict[str, Any], language: str, country: str,
      currency: str) -> optimization_result_counts.OptimizationResultCounts:
    """Runs the optimization.

    Fixes invalid condition values.
    See above for the definition of an invalid condition value.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected by this optimization.
    """
    num_of_products_optimized = 0
    num_of_products_excluded = 0

    self._condition_config = config_parser.get_config_contents(
        _CONDITION_OPTIMIZER_CONFIG_OVERRIDE_KEY,
        _CONDITION_OPTIMIZER_CONFIG_FILENAME.format(language))
    self._gpc_id_to_string_converter = gpc_id_to_string_converter.GPCConverter(
        _GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME.format(language))

    for entry in product_batch['entries']:

      if (optimization_util.optimization_exclusion_specified(
          entry, self._OPTIMIZER_PARAMETER)):
        num_of_products_excluded += 1
        continue

      product = entry['product']
      google_product_category = product.get('googleProductCategory', '')
      gpc_string = self._gpc_id_to_string_converter.convert_gpc_id_to_string(
          google_product_category)
      if self._is_google_product_category_excluded(gpc_string):
        logging.info(
            'Product ID: %s With Category %s was flagged for exclusion '
            ' of the condition check', product.get('offerId', ''), gpc_string)
        continue

      used_tokens = set(
          token.lower() for token in self._condition_config['used_tokens'])
      if product.get('condition', '') == _NEW:
        # Category format must follow the official spec to be converted a list.
        # Ref: https://support.google.com/merchants/answer/6324436?hl=en.
        product_categories = gpc_string.split(' > ')
        if isinstance(product_categories, list) and product_categories:
          lowest_level_category = product_categories[-1]
          category_specific_tokens = self._get_tokens_for_category(
              lowest_level_category)

          if category_specific_tokens:
            category_specific_tokens = set(
                token.lower() for token in category_specific_tokens)
            used_tokens.update(category_specific_tokens)

        # Search for used tokens in both title and description and reset the
        # condition to used if any were detected.
        product_title = product.get('title', '')
        product_description = product.get('description', '')
        if self._field_contains_used_tokens(
            product_title, used_tokens) or self._field_contains_used_tokens(
                product_description, used_tokens):
          product['condition'] = _USED
          logging.info('Modified item %s: Setting new product to used.',
                       product.get('offerId', ''))
          num_of_products_optimized += 1
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.SANITIZED)
    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)

  def _is_google_product_category_excluded(
      self, google_product_category: str) -> bool:
    """Checks if the provided category was found in the exclusions config dict.

    Args:
      google_product_category: A string representing the product category.

    Returns:
      True if the given category was found in the condition config's list of
      categories to exclude from being optimized for condition due to those
      categories being at higher risk of containing false-positives.
    """
    excluded_categories = self._condition_config.get(
        'excluded_product_categories', [])

    # Ensure that the exclude category from the config matches the product's
    # category from the beginning of the string in order to support an entire
    # category family being matched, as well as enforcing avoidance of unrelated
    # matches if only a sub-category was specified.
    return any(
        google_product_category.startswith(category_to_exclude)
        for category_to_exclude in excluded_categories)

  def _field_contains_used_tokens(self, field_text: str,
                                  used_tokens: Set[str]) -> bool:
    """Checks if the provided field contains any terms in the given set.

    Args:
      field_text: A string representing the value of a product field.
      used_tokens: A set representing used condition indicators.

    Returns:
      True if any term was found in the target product field, otherwise False.
    """
    return any(token in field_text.lower() for token in used_tokens)

  def _get_tokens_for_category(self, product_category: str) -> List[str]:
    """Gets the values in a list of dictionaries if the provided category was found.

    Args:
      product_category: The product's lowest-level category.

    Returns:
      A list of the tokens of the matching category, or an empty list.
    """
    category_mappings = self._condition_config['target_product_categories']
    return category_mappings.get(product_category, [])
