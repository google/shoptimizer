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

"""A module for Shoptimizer API that excludes products from Shopping Ads.

Certain products can be disapproved if they were detected as not meant for
Shopping, so this optimizer will exclude them from the Shopping Ads destination.
"""

import logging
from typing import Any, Dict, Optional, Set

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import config_parser
from util import optimization_util

_EXCLUDED_DESTINATIONS_KEY = 'excludedDestinations'
_INCLUDED_DESTINATIONS_KEY = 'includedDestinations'

_SHOPPING_ADS_DESTINATION = 'Shopping_ads'
_FREE_LISTINGS_DESTINATION = 'Free_listings'

_SHOPPING_EXCLUSION_OPTIMIZER_CONFIG_FILE_NAME = (
    'shopping_exclusion_optimizer_config_{}')
_SHOPPING_EXCLUSION_OPTIMIZER_CONFIG_OVERRIDE_KEY = (
    'shopping_exclusion_optimizer_config_override')


class ShoppingExclusionOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that detects and excludes products from Shopping Ads."""

  _OPTIMIZER_PARAMETER: str = 'shopping-exclusion-optimizer'
  shopping_removal_config: Optional[Dict[str, Any]] = None
  shopping_removal_patterns_exact_match: Optional[Set[str]] = None

  def _optimize(
      self, product_batch: Dict[str, Any], language: str, country: str,
      currency: str) -> optimization_result_counts.OptimizationResultCounts:
    """Runs the optimization.

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

    self._shopping_exclusion_config = config_parser.get_config_contents(
        _SHOPPING_EXCLUSION_OPTIMIZER_CONFIG_OVERRIDE_KEY,
        _SHOPPING_EXCLUSION_OPTIMIZER_CONFIG_FILE_NAME.format(language))

    self.shopping_removal_patterns_exact_match = frozenset(
        self._shopping_exclusion_config.get(
            'shopping_exclusion_patterns_exact_match', []))

    for entry in product_batch['entries']:

      if (optimization_util.optimization_exclusion_specified(
          entry, self._OPTIMIZER_PARAMETER)):
        num_of_products_excluded += 1
        continue

      product = entry['product']

      if self._is_non_shopping_product(product.get('title', '')):
        _normalize_all_destinations(product)

        if isinstance(product.get(_EXCLUDED_DESTINATIONS_KEY), list):
          if _SHOPPING_ADS_DESTINATION not in product[
              _EXCLUDED_DESTINATIONS_KEY]:
            product[_EXCLUDED_DESTINATIONS_KEY].append(
                _SHOPPING_ADS_DESTINATION)
          if _FREE_LISTINGS_DESTINATION not in product[
              _EXCLUDED_DESTINATIONS_KEY]:
            product[_EXCLUDED_DESTINATIONS_KEY].append(
                _FREE_LISTINGS_DESTINATION)
        else:
          product[_EXCLUDED_DESTINATIONS_KEY] = [
              _SHOPPING_ADS_DESTINATION, _FREE_LISTINGS_DESTINATION
          ]

        if isinstance(product.get(_INCLUDED_DESTINATIONS_KEY), list):
          if _SHOPPING_ADS_DESTINATION in product[_INCLUDED_DESTINATIONS_KEY]:
            product[_INCLUDED_DESTINATIONS_KEY].remove(
                _SHOPPING_ADS_DESTINATION)
          if _FREE_LISTINGS_DESTINATION in product[_INCLUDED_DESTINATIONS_KEY]:
            product[_INCLUDED_DESTINATIONS_KEY].remove(
                _FREE_LISTINGS_DESTINATION)

        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.SANITIZED)
        logging.info(
            'Product %s was detected as not meant for Shopping Ads, so excluding from the Shopping Ads destination',
            product.get('offerId'))

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)

  def _is_non_shopping_product(self, product_field: str) -> bool:
    """Determines if a product's field contains text indicating it is not intended for Shopping.

    Args:
      product_field: A field of a product to check for existence Shopping
        exclusion terms.

    Returns:
      True if the given field was detected to have Shopping exclusion terms,
      otherwise false.
    """
    if any(shopping_exclusion_pattern in product_field
           for shopping_exclusion_pattern in
           self.shopping_removal_patterns_exact_match):
      return True
    else:
      return False


def _normalize_all_destinations(product: Dict[str, Any]) -> None:
  """Normalizes the format of shopping destinations in both 'excludedDestinations' and 'includedDestinations' fields."""
  for key in (_EXCLUDED_DESTINATIONS_KEY, _INCLUDED_DESTINATIONS_KEY):
    _normalize_destinations(product, key)


def _normalize_destinations(product: Dict[str, Any], key: str) -> None:
  """Normalizes the format of shopping destinations to be consistent with the help page: https://support.google.com/merchants/answer/6324486?hl=en.

  This function replaces a space in destinations with an underscore.
  e.g. 'Shopping ads' -> 'Shopping_ads'

  Args:
    product: Product data.
    key: A field name of shopping destinations. It must be either
      'excludedDestinations' or 'includedDestinations'.
  """
  normalized_destinations = []
  if isinstance(product.get(key), list):
    for destination in product[key]:
      normalized_destination = destination.replace(' ', '_')
      normalized_destinations.append(normalized_destination)
    product[key] = normalized_destinations
