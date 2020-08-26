# coding=utf-8
# Copyright 2020 Google LLC.
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
"""A module for Shoptimizer API that fixes title values.

Reference: https://support.google.com/merchants/answer/6324415

Products whose titles are too long or truncated forms of the item's description
cause poor performance. This optimizer will shorten the title if it's too long
and populate title with description if it was detected to be
truncated.
"""

import logging
import re
from typing import Any, Dict

from optimizers_abstract import base_optimizer

_MAX_TITLE_LENGTH: int = 150


class TitleLengthOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that fixes title length."""

  _OPTIMIZER_PARAMETER = 'title-length-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    """Runs title length optimization.

    This method optimizes the title by executing following processes:
    - Truncates title to the max title length if its length exceeds the max
    value.
    - Populate title with description if title is truncated from description.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected by this optimization.
    """
    num_of_products_optimized: int = 0

    entry: Dict[str, Any]
    for entry in product_batch['entries']:
      product = entry['product']
      item_id: str = product.get('offerId', '')
      title: str = product.get('title', '')
      trailing_dots_removed_title: str = re.sub('[.…]+$', '', title)
      description: str = product.get('description', '')

      if len(title) > _MAX_TITLE_LENGTH:
        product['title'] = title[:_MAX_TITLE_LENGTH]
        logging.info('Modified item %s: Truncating title: %s', item_id,
                     product['title'])
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.SANITIZED)

      elif trailing_dots_removed_title != description and description.startswith(
          trailing_dots_removed_title):
        product['title'] = description[:_MAX_TITLE_LENGTH]
        logging.info(
            'Modified item %s: Populating title with '
            'description due to detected title truncation: %s', item_id,
            product['title'])
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.OPTIMIZED)

    return num_of_products_optimized
