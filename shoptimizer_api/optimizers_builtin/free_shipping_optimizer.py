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

"""A module for Shoptimizer API that sets free shipping when applicable.

Reference: https://support.google.com/merchants/answer/6324484

This module sets the free shipping attribute to 0 by detecting regex patterns in
the config file that represents free shipping in the title of a product. It does
not set free shipping when it detects an exclusion pattern (e.g. Except Okinawa)
even if a free shipping pattern was found in the title.

This module uses a config file located in
./config/free_shipping_optimizer_config_{language code}.json.

Make sure this optimizer is called before title-optimizer because
title-optimizer removes patterns representing free shipping.
"""

import logging
import re
from typing import Any, Dict, List

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import config_parser
from util import optimization_util

_FREE_SHIPPING_OPTIMIZER_CONFIG_NAME = 'free_shipping_optimizer_config_{}'
_FREE_SHIPPING_OPTIMIZER_CONFIG_OVERRIDE_KEY = (
    'free_shipping_optimizer_config_override')


class FreeShippingOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that optimizes shipping field when shipping is free."""

  _OPTIMIZER_PARAMETER: str = 'free-shipping-optimizer'

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

    self._free_shipping_config = config_parser.get_config_contents(
        _FREE_SHIPPING_OPTIMIZER_CONFIG_OVERRIDE_KEY,
        _FREE_SHIPPING_OPTIMIZER_CONFIG_NAME.format(language))

    for entry in product_batch['entries']:

      if (optimization_util.optimization_exclusion_specified(
          entry, self._OPTIMIZER_PARAMETER)):
        num_of_products_excluded += 1
        continue

      product = entry['product']

      original_shipping = product.get('shipping')

      title_contains_free_shipping_pattern = self._title_contains_pattern(
          product, 'free_shipping_patterns')
      title_contains_exclusion_pattern = self._title_contains_pattern(
          product, 'shipping_exclusion_patterns')

      if title_contains_free_shipping_pattern and not title_contains_exclusion_pattern:
        _update_shipping_field_to_zero(product, country, currency)

      if product.get('shipping') != original_shipping:
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.OPTIMIZED)

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)

  def _has_free_shipping_pattern(self, product: Dict[str, Any]) -> bool:
    """Checks if any pattern that represents free shipping is in the title of a given product.

    Args:
      product: Product data.

    Returns:
      Whether any pattern that represents free shipping is in the title of a
      given product or not.
    """
    return self._title_contains_pattern(product, 'free_shipping_patterns')

  def _has_exceptional_pattern(self, product: Dict[str, Any]) -> bool:
    """Checks if any exceptional pattern for free shipping is in the title of a given product.

    Args:
      product: Product data.

    Returns:
      Whether any exceptional pattern for free shipping is in the title of a
      given product or not.
    """
    return self._title_contains_pattern(product, 'shipping_exclusion_patterns')

  def _title_contains_pattern(self, product: Dict[str, Any],
                              config_key: str) -> bool:
    """Checks if any pattern in the config is in the title of a given product.

    Args:
      product: Product data.
      config_key: A key in the config file whose value includes regex patterns.

    Returns:
      Whether any pattern in the config is in the title of a given product or
      not.
    """
    title = product.get('title', '')
    for pattern in self._free_shipping_config.get(config_key):
      if re.search(pattern, title):
        return True
    return False


def _update_shipping_field_to_zero(product: Dict[str, Any], country: str,
                                   currency: str) -> None:
  """Adds a free shipping object to shipping field of a product.

  Args:
    product: Product data.
    country: A country code.
    currency: A currency code.
  """
  shipping_field = product.get('shipping', [])

  if _free_shipping_already_exists(shipping_field, country, currency):
    return

  shipping_field.append(
      dict(country=country, price=dict(value='0', currency=currency)))
  product['shipping'] = shipping_field

  logging.info('Modified item %s: Setting free shipping. Title is %s',
               product.get('offerId', ''), product.get('title', ''))


def _free_shipping_already_exists(shipping_field: List[Dict[str, Any]],
                                  country: str, currency: str) -> bool:
  """Checks if free shipping object to the given country and currency is already in shipping field.

  Args:
    shipping_field: The content of shipping field.
    country: A country code.
    currency: A currency code.

  Returns:
    Whether free shipping object is already in shipping field or not.
  """
  for shipping_object in shipping_field:
    existing_price_currency = shipping_object.get('price', {}).get('currency')
    existing_country = shipping_object.get('country')
    if existing_price_currency.casefold() == currency.casefold(
    ) and existing_country.casefold() == country.casefold():
      return True
  return False
