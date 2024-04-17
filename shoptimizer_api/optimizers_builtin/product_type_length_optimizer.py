# coding=utf-8
# Copyright 2025 Google LLC.
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

"""A module for Shoptimizer API that fixes the productTypes attribute.

Reference: https://support.google.com/merchants/answer/6324406

Products whose productTypes field has too many elements cause disapproval.
So this optimizer will remove the extra elements in productTypes if it has more
than 10 elements.
(Note: the official doc specifies a limit of 5 product types but the actual
limit is 10 as of 20200331)
"""
import logging
from typing import Any, Dict

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import optimization_util

_MAX_LIST_LENGTH: int = 10
_SEPARATOR: str = ','


class ProductTypeLengthOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that fixes the length of productTypes."""

  _OPTIMIZER_PARAMETER = 'product-type-length-optimizer'

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

    for entry in product_batch['entries']:

      if (optimization_util.optimization_exclusion_specified(
          entry, self._OPTIMIZER_PARAMETER)):
        num_of_products_excluded += 1
        continue

      product = entry['product']
      if 'productTypes' in product:
        product_types = product.get('productTypes', [])

        optimized_product_types = (
            optimization_util.cut_list_to_limit_list_length(
                product_types, _MAX_LIST_LENGTH))

        if optimized_product_types != product_types:
          product['productTypes'] = optimized_product_types
          logging.info(
              'Modified item %s: Removing the last items from productTypes: %s',
              product.get('offerId', ''), product_types)
          num_of_products_optimized += 1
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.SANITIZED)

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)
