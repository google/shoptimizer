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

"""A module for Shoptimizer API that excludes products from Shopping Ads.

Certain products can be disapproved if they were detected as not meant for
Shopping, so this optimizer will exclude them from the Shopping Ads destination.
"""

import logging
from typing import Any, Dict, Optional, Set

import flask

from optimizers_abstract import base_optimizer

_SHOPPING_ADS_DESTINATION = 'Shopping ads'


class ShoppingExclusionOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that detects and excludes products from Shopping Ads."""

  _OPTIMIZER_PARAMETER: str = 'shopping-exclusion-optimizer'
  shopping_removal_config: Optional[Dict[str, Any]] = None
  shopping_removal_patterns_exact_match: Optional[Set[str]] = None

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
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

    self._shopping_exclusion_config = flask.current_app.config.get(
        'CONFIGS', {}).get(f'shopping_exclusion_optimizer_config_{language}',
                           {})
    self.shopping_removal_patterns_exact_match = frozenset(
        self._shopping_exclusion_config.get(
            'shopping_exclusion_patterns_exact_match', []))

    for entry in product_batch['entries']:
      product = entry['product']

      if self._is_non_shopping_product(product.get('title', '')):
        if isinstance(
            product.get('excludedDestinations'), list
        ) and _SHOPPING_ADS_DESTINATION not in product['excludedDestinations']:
          product['excludedDestinations'].append(_SHOPPING_ADS_DESTINATION)
        else:
          product['excludedDestinations'] = [_SHOPPING_ADS_DESTINATION]

        if isinstance(
            product.get('includedDestinations'), list
        ) and _SHOPPING_ADS_DESTINATION in product['includedDestinations']:
          product['includedDestinations'].remove(_SHOPPING_ADS_DESTINATION)

        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.SANITIZED)
        logging.info(
            'Product %s was detected as not meant for Shopping Ads, so excluding from the Shopping Ads destination',
            product.get('offerId'))

    return num_of_products_optimized

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
