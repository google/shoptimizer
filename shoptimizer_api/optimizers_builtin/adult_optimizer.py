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

"""An optimizer that fixes unset adult values.

Reference: https://support.google.com/merchants/answer/6150138

If a product in the request is determined to be in a category that requires
the "adult" attribute to be set to True on the Content API request, this
optimizer will set the "adult" attribute to True for that product.
"""
import logging
from typing import AbstractSet, Any, Mapping, Sequence
from flask import current_app

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import optimization_util


class AdultOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that fixes invalidly-set adult fields."""

  _OPTIMIZER_PARAMETER = 'adult-optimizer'
  _adult_config = None
  _adult_types = None

  def _optimize(
      self, product_batch: Mapping[str, Any], language: str, country: str,
      currency: str) -> optimization_result_counts.OptimizationResultCounts:
    """Runs the optimization.

    Fixes invalid adult values.
    See above for the definition of an invalid adult value.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected by this optimization.
    """
    self._adult_config = current_app.config.get('CONFIGS', {}).get(
        f'adult_optimizer_config_{language}', {})
    self._adult_types = frozenset(
        self._adult_config.get('adult_product_types', []))

    num_of_products_optimized = 0
    num_of_products_excluded = 0

    for entry in product_batch['entries']:

      if (optimization_util.optimization_exclusion_specified(
          entry, self._OPTIMIZER_PARAMETER)):
        num_of_products_excluded += 1
        continue

      product = entry['product']
      product_types = product.get('productTypes', [])
      product_category = product.get('googleProductCategory', '')
      category_specific_tokens = self._get_tokens_for_category(product_category)
      is_adult = product.get('adult', False)

      # Product Types can directly determine adult category or not.
      if not is_adult and self._is_product_type_adult(product_types):
        logging.info('Product ID: %s With type %s was determined to be adult',
                     product['offerId'], product_types)
        product['adult'] = True
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.SANITIZED)
      # Otherwise a target GPC combined with specific tokens in the title or
      # description can determine if the product should have the adult flag set.
      elif not is_adult and category_specific_tokens:
        product_should_be_adult = False

        # If only a wildcard was specified for the tokens in the config, any
        # product in this category should have the adult attribute set.
        if len(category_specific_tokens
              ) == 1 and category_specific_tokens[0] == '*':
          product_should_be_adult = True
        else:
          adult_tokens = set(
              token.lower() for token in category_specific_tokens)
          product_title = product.get('title', '')
          product_description = product.get('description', '')
          if self._field_contains_adult_tokens(
              product_title, adult_tokens) or self._field_contains_adult_tokens(
                  product_description, adult_tokens):
            product_should_be_adult = True

        if product_should_be_adult:
          product['adult'] = True
          num_of_products_optimized += 1
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.SANITIZED)

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)

  def _is_product_type_adult(self, product_types: Sequence[str]) -> bool:
    """Checks if the provided product type was found in the adult config dict.

    Args:
      product_types: A List of strings representing the product types.

    Returns:
      True if the given product type was found in the adult config's list of
      product types, otherwise False.
    """
    return any(
        product_type in self._adult_types for product_type in product_types)

  def _field_contains_adult_tokens(self, field_text: str,
                                   adult_tokens: AbstractSet[str]) -> bool:
    """Checks if the provided field contains adult terms specified in the adult config file.

    Args:
      field_text: A string representing the value of a product field.
      adult_tokens: A set of strings representing adult product indicators.

    Returns:
      True if the given product title contained any terms defined in the adult
      config file for a specific google product category, otherwise false.
    """
    return any(token in field_text.lower() for token in adult_tokens)

  def _get_tokens_for_category(self, product_category: str) -> Sequence[str]:
    """Gets the values in a list of tokens if the provided category was found.

    Args:
      product_category: The product's category.

    Returns:
      A list of the tokens of the matching category, or an empty list.
    """
    adult_categories = self._adult_config['adult_google_product_categories']
    for adult_category in adult_categories:
      if product_category.startswith(adult_category):
        return adult_categories.get(adult_category, [])
