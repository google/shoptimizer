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

"""A module for Shoptimizer API that sanitizes promo text in product titles."""

import logging
from typing import Any, Dict

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import optimization_util
from util import promo_text_remover


class PromoTextRemovalOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that removes promotional text from the product title."""

  _OPTIMIZER_PARAMETER: str = 'promo-text-removal-optimizer'

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
      original_title = product.get('title', '')

      _remove_unnecessary_text(product, language)

      if product.get('title', '') != original_title:
        logging.info('Modified item %s: Removed promo text, new title is: %s',
                     product.get('offerId', ''), product.get('title', ''))
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.SANITIZED)

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)


def _remove_unnecessary_text(product: Dict[str, Any], language: str) -> None:
  """Removes unnecessary text from the title.

  Args:
    product: Product data.
    language: The language to use for this optimizer.
  """
  remover = promo_text_remover.PromoTextRemover(language=language)
  remover.remove_text_from_field(product, 'title')
