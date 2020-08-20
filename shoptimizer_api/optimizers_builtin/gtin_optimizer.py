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
"""A module for Shoptimizer API that fixes invalid gtin values.

Reference: https://support.google.com/merchants/answer/6324461

The last digit of the gtin must match the formula defined here:
https://www.gs1.org/services/how-calculate-check-digit-manually

If it fails this check, this optimizer will remove the gtin field from the
product to prevent the product from being disapproved in Merchant Center.
"""
import logging
import math
from typing import Any, Dict

from optimizers_abstract import base_optimizer

_VALID_GTIN_LENGTHS = [8, 12, 13, 14]


class GTINOptimizer(base_optimizer.BaseOptimizer):
  """"An optimizer that fixes invalid gtin values."""

  _OPTIMIZER_PARAMETER = 'gtin-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str, _) -> int:
    """Runs the optimization.

    Fixes invalid gtin fields.
    See above for the definition of an invalid gtin field.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.

    Returns:
      The number of products affected by this optimization: int
    """
    num_of_products_optimized = 0
    for entry in product_batch['entries']:
      product = entry['product']
      if 'gtin' in product:
        gtin = product.get('gtin', '')

        if _gtin_passes_format_check(gtin) and _gtin_passes_checksum(gtin):
          continue

        violating_gtin = product.get('gtin', '')
        del product['gtin']
        logging.info(
            'Modified item %s: Cleared invalid gtin: %s to '
            'prevent disapproval', product.get('offerId', ''), violating_gtin)
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.SANITIZED)
        num_of_products_optimized += 1

    return num_of_products_optimized


def _gtin_passes_format_check(gtin: str) -> bool:
  """Determines if the provided gtin violates basic sanity checks.

  Args:
    gtin: a string representing the product's GTIN

  Returns:
    Boolean, True if the gtin passes the validations, otherwise false.
  """
  if not gtin.isdigit() or len(
      gtin) not in _VALID_GTIN_LENGTHS or _contains_repeating_digits(
          gtin[:-1]) or _contains_sequential_digits(gtin):
    return False
  return True


def _gtin_passes_checksum(gtin: str) -> bool:
  """Determines if the provided gtin violates the check digit calculation.

  Args:
    gtin: a string representing the product's GTIN

  Returns:
    Boolean, True if the gtin passes check digit validation, otherwise false.
  """
  padded_gtin = gtin.zfill(14)
  existing_check_digit = int(padded_gtin[-1])
  target_check_digit = _calculate_check_digit(padded_gtin[:-1])
  return target_check_digit == existing_check_digit


def _calculate_check_digit(partial_gtin: str) -> int:
  """Calculates the expected check digit of a GTIN (without the last digit).

  Args:
    partial_gtin: a string representing a product GTIN without the check digit.

  Returns:
    Int, the calculated expected check digit of the input GTIN.
  """
  odds = list(partial_gtin[::2])
  evens = [int(x) for x in list(partial_gtin[1::2])]
  odds_times_three = [int(x) * 3 for x in odds]
  sum_mults = sum(evens) + sum(odds_times_three)
  check_digit = _round_up(sum_mults) - sum_mults
  return check_digit


def _round_up(x) -> int:
  return int(math.ceil(x / 10.0)) * 10


def _contains_repeating_digits(gtin: str) -> bool:
  return gtin.count(gtin[0]) == len(gtin)


def _contains_sequential_digits(gtin: str) -> bool:
  return gtin.startswith('123456789')
