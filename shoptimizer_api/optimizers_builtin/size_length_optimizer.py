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

# python3
"""A module for Shoptimizer API that fixes the length of the sizes attribute.

Reference: https://support.google.com/merchants/answer/6324492

The sizes attribute consists of a list containing a single string.
If this string is over 100 characters, the product will be disapproved.
This optimizer will trim the sizes attribute string to 100 characters and
ensure the sizes attribute only contains one value.
"""
import logging
from typing import Any, Dict

from optimizers_abstract import base_optimizer

_MAX_SIZE_LENGTH: int = 100


class SizeLengthOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that fixes the length of the sizes attribute."""

  _OPTIMIZER_PARAMETER = 'size-length-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str, _) -> int:
    """Runs size length optimization.

    Fixes invalid size values.
    See above for the definition of an invalid size value.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.

    Returns:
      The number of products affected by this optimization.
    """
    num_of_products_optimized = 0

    for entry in product_batch['entries']:
      product = entry['product']
      if 'sizes' in product and product.get('sizes', []):
        size = product['sizes'][0]

        if not size:
          continue

        if len(size) > _MAX_SIZE_LENGTH or len(product.get('sizes', [])) > 1:
          product['sizes'] = [size[:_MAX_SIZE_LENGTH]]
          item_id = product.get('offerId', '')
          logging.info(
              'Modified item %s: Clearing identifierExists '
              'to prevent disapproval', item_id)
          num_of_products_optimized += 1
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.SANITIZED)

    return num_of_products_optimized
