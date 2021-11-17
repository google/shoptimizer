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

"""A module for Shoptimizer API that optimizes the product description.

Reference: https://support.google.com/merchants/answer/6324468

This module appends product fields to the description, or creates a
description from product fields if no description exists. This is expected
to improve product performance. The following fields are appended if they
contain values or could be mined from the product:
  - gender
  - color
  - sizes
  - brand
"""

import logging
from typing import Any, Dict

import constants

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import optimization_util

_MAX_DESCRIPTION_LENGTH: int = 5000


class DescriptionOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that optimizes the description."""

  _OPTIMIZER_PARAMETER: str = 'description-optimizer'

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

      original_description = product.get('description', '')

      fields_to_append_to_description = self._get_fields_to_append_to_description(
          product['offerId'])
      optimized_description = _create_optimized_description(
          original_description, fields_to_append_to_description)

      if original_description != optimized_description:
        _update_product_description(product, optimized_description)
        num_of_products_optimized += 1

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)

  def _get_fields_to_append_to_description(self,
                                           product_id: str) -> Dict[str, Any]:
    """Returns the fields to append to the description for a given product id.

    Args:
      product_id: The id of the product being optimized.

    Returns:
      The fields to append to the description for this product, or an empty list
      if no mined fields could be found for this product.
    """
    if not self._mined_attributes or product_id not in self._mined_attributes:
      return {}

    return self._mined_attributes.get(product_id)


def _create_optimized_description(original_description: str,
                                  fields: Dict[str, Any]) -> str:
  """Appends the fields to the description.

  Args:
    original_description: The original product description.
    fields: the fields to be appended.

  Returns:
    The original description with as many fields as possible appended.
  """
  if not fields:
    return original_description

  fields_to_append_to_description = []
  for _, mined_attribute_values in fields.items():
    if isinstance(mined_attribute_values, str):
      fields_to_append_to_description.append(mined_attribute_values)
    elif isinstance(mined_attribute_values, list):
      fields_to_append_to_description.extend(mined_attribute_values)

  field_with_keywords_appended = optimization_util.append_keywords_to_field(
      original_description, fields_to_append_to_description,
      len(original_description), _MAX_DESCRIPTION_LENGTH,
      constants.ALL_ALPHABETIC_CLOTHING_SIZES)

  return field_with_keywords_appended


def _update_product_description(product: Dict[str, Any],
                                optimized_description: str) -> None:
  """Updates the description for the given product and sets tracking/logging.

  Args:
    product: Product data.
    optimized_description: The new product description.
  """
  product['description'] = optimized_description
  base_optimizer.set_optimization_tracking(product, base_optimizer.OPTIMIZED)
  logging.info('Modified item %s: Appended field values to description: %s',
               product['offerId'], product['description'])
