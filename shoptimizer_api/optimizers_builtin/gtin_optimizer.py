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
"""A module for Shoptimizer API that fixes invalid gtin values.

Reference: https://support.google.com/merchants/answer/6324461

This optimizer does several validations on the gtin value:

1. The gtin must consist of integers, and fall within a range of valid lengths.

2. The gtin must not start with the bulk indicator digit (9):
https://support.google.com/merchants/answer/6286298?hl=en

3. The gtin must not use the reserved range for its prefix:
https://support.google.com/merchants/answer/7000684?hl=en

4. The gtin must not use the coupon range for its prefix:
https://support.google.com/merchants/answer/6286302?hl=en

5. The last digit of the gtin must match the formula defined here:
https://www.gs1.org/services/how-calculate-check-digit-manually

If it fails these checks, this optimizer will remove the gtin field from the
product to prevent the product from being disapproved in Merchant Center.
"""
import logging
import math
from typing import Any, Dict

from optimizers_abstract import base_optimizer

_VALID_GTIN_LENGTHS = [8, 12, 13, 14]
_COUPON_PREFIXES = ['981', '982', '983', '984', '99', '05']
_RESTRICTED_PREFIXES = ['020-029', '040-049', '200-299']
_INVALID_BULK_INDICATOR = '9'


class GTINOptimizer(base_optimizer.BaseOptimizer):
  """"An optimizer that fixes invalid gtin values."""

  _OPTIMIZER_PARAMETER = 'gtin-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    """Runs the optimization.

    Fixes invalid gtin fields.
    See above for the definition of an invalid gtin field.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected by this optimization: int
    """
    num_of_products_optimized = 0
    for entry in product_batch['entries']:
      product = entry['product']
      if 'gtin' in product:
        gtin = product.get('gtin', '')

        violates_any_gtin_check = (_gtin_fails_format_check(gtin) or
                                   _gtin_uses_bulk_indicator(gtin) or
                                   _gtin_uses_reserved_range(gtin) or
                                   _gtin_uses_coupon_range(gtin) or
                                   _gtin_fails_checksum(gtin))
        if violates_any_gtin_check:
          _remove_gtin(product)
          num_of_products_optimized += 1

    return num_of_products_optimized


def _remove_gtin(product: Dict[str, Any]) -> None:
  """Clears the gtin value from the product.

  Args:
    product: A dictionary representing a single shopping product.
  """
  violating_gtin = product.get('gtin', '')
  del product['gtin']
  logging.info(
      'Modified item %s: Cleared invalid gtin: %s to '
      'prevent disapproval', product.get('offerId', ''), violating_gtin)
  base_optimizer.set_optimization_tracking(product, base_optimizer.SANITIZED)


def _gtin_uses_bulk_indicator(gtin: str) -> bool:
  """Determines if the provided gtin violates the bulk indicator digit check.

  Args:
    gtin: a string representing the product's GTIN.

  Returns:
    True if the indicator digit is 9, otherwise False.
  """
  return len(gtin) == 14 and gtin[0] == _INVALID_BULK_INDICATOR


def _gtin_uses_reserved_range(gtin: str) -> str:
  """Determines if the provided gtin violates the reserved prefix check.

  Args:
    gtin: a string representing the product's GTIN.

  Returns:
    True if the prefix is in a reserved prefix range, otherwise False.
  """
  company_prefix = int(gtin[1:4])
  for restricted_prefix in _RESTRICTED_PREFIXES:
    if company_prefix >= int(
        restricted_prefix.split('-')[0]) and company_prefix <= int(
            restricted_prefix.split('-')[1]):
      return True
  return False


def _gtin_uses_coupon_range(gtin: str) -> bool:
  """Determines if the provided gtin violates the coupon prefix check.

  Args:
    gtin: a string representing the product's GTIN.

  Returns:
    True if the prefix is in a coupon prefix range, otherwise False.
  """
  return gtin[1:].startswith(tuple(_COUPON_PREFIXES))


def _gtin_fails_format_check(gtin: str) -> bool:
  """Determines if the provided gtin violates basic sanity checks.

  Args:
    gtin: a string representing the product's GTIN

  Returns:
    True if the gtin fails the validations, otherwise False.
  """
  if not gtin.isdigit() or len(
      gtin) not in _VALID_GTIN_LENGTHS or _contains_repeating_digits(
          gtin[:-1]) or _contains_sequential_digits(gtin):
    return True
  return False


def _gtin_fails_checksum(gtin: str) -> bool:
  """Determines if the provided gtin violates the check digit calculation.

  Args:
    gtin: a string representing the product's GTIN

  Returns:
    True if the gtin fails check digit validation, otherwise False.
  """
  padded_gtin = gtin.zfill(14)
  existing_check_digit = int(padded_gtin[-1])
  target_check_digit = _calculate_check_digit(padded_gtin[:-1])
  return target_check_digit != existing_check_digit


def _calculate_check_digit(partial_gtin: str) -> int:
  """Calculates the expected check digit of a GTIN (without the last digit).

  Args:
    partial_gtin: a string representing a product GTIN without the check digit.

  Returns:
    the calculated expected check digit of the input GTIN.
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
