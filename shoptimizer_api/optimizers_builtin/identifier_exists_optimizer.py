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

"""A module for Shoptimizer API that fixes identifierExists values.

Reference: https://support.google.com/merchants/answer/6324478
and https://support.google.com/merchants/answer/9464748

Products that have a brand, mpn, or gtin set and identifierExists as "false"
could cause disapproval, so this optimizer will delete the identifierExists
value in these cases, which defaults the value to true in Content API.
"""
import logging
from typing import Any, Dict

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import optimization_util


class IdentifierExistsOptimizer(base_optimizer.BaseOptimizer):
  """"An optimizer that fixes invalid identifierExists values."""

  _OPTIMIZER_PARAMETER = 'identifier-exists-optimizer'

  def _optimize(
      self, product_batch: Dict[str, Any], language: str, country: str,
      currency: str) -> optimization_result_counts.OptimizationResultCounts:
    """Runs the optimization.

    Removes invalid identifierExists fields.
    See above for the definition of an invalid identifierExists field.

    Args:
      product_batch:  A batch of product data.
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
      identifier_exists = product.get('identifierExists', True)
      brand = product.get('brand', '')
      gtin = product.get('gtin', '')
      mpn = product.get('mpn', '')
      if not identifier_exists and (brand or gtin or mpn):
        item_id = product.get('offerId', '')
        logging.info(
            'Modified item %s: Clearing identifierExists '
            'to prevent disapproval', item_id)
        # Delete field from the request which defaults it to true.
        del product['identifierExists']
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.SANITIZED)
    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)
