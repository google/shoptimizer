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

"""An optimizer that returns the product data without modifying it."""
from typing import Any

from models import optimization_result_counts
from optimizers_abstract import base_optimizer


class IdentityOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that returns the product data without modifying it."""

  _OPTIMIZER_PARAMETER = 'identity-optimizer'

  def _optimize(
      self,
      product_batch: dict[str, Any],
      language: str,
      country: str,
      currency: str,
  ) -> optimization_result_counts.OptimizationResultCounts:
    """Runs identity optimization.

    This optimizer does not transform the product data and is only
    used to demonstrate the logical structure of an optimizer.

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

    # Logic can be added like this --
    # for entry in data['entries']:
    #  product = entry['product']
    #  product['identity'] = 'identity'
    #  num_of_products_optimized = num_of_products_optimized + 1
    #  base_optimizer.set_optimization_tracking(product,
    #                                           base_optimizer.SANITIZED)
    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)
