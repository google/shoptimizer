# coding=utf-8
# Copyright 2024 Google LLC.
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

"""A module for Shoptimizer API that fixes the length of the color attribute.

Reference: https://support.google.com/merchants/answer/6324487

This module does three things:
1. Ensures the total length of the color attribute is <= 100 characters
2. Removes any color with a length > 40 characters
3. Ensures there are no more than 3 colors in the list of colors
If the above conditions are not met, the product will be disapproved.
"""
from typing import Any, Dict

import constants

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import optimization_util

_SEPARATOR: str = '/'


class ColorLengthOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that fixes the length of the color attribute."""

  _OPTIMIZER_PARAMETER = 'color-length-optimizer'

  def _optimize(
      self, product_batch: Dict[str, Any], language: str, country: str,
      currency: str) -> optimization_result_counts.OptimizationResultCounts:
    """Runs the optimization.

    Fixes invalid color fields.
    See above for the definition of an invalid color field.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected and excluded by this optimization.
    """
    num_of_products_optimized = 0
    num_of_products_excluded = 0

    for entry in product_batch['entries']:

      if (optimization_util.optimization_exclusion_specified(
          entry, self._OPTIMIZER_PARAMETER)):
        num_of_products_excluded += 1
        continue

      product = entry['product']
      if 'color' in product:
        original_colors = product.get('color', '')

        colors = original_colors.split(_SEPARATOR)

        optimized_colors = optimization_util.cut_list_elements_over_max_length(
            colors, constants.MAX_COLOR_STR_LENGTH_FOR_EACH)

        optimized_colors = optimization_util.cut_list_to_limit_list_length(
            optimized_colors, constants.MAX_COLOR_COUNT)

        optimized_colors = optimization_util.cut_list_to_limit_concatenated_str_length(
            optimized_colors, _SEPARATOR,
            constants.MAX_COLOR_STR_LENGTH_IN_TOTAL)

        optimized_colors = _SEPARATOR.join(optimized_colors)

        if original_colors != optimized_colors:
          product['color'] = optimized_colors
          num_of_products_optimized += 1
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.SANITIZED)

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)
