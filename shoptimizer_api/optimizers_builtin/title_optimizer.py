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
"""A module for Shoptimizer API that optimizes title values.

Reference: https://support.google.com/merchants/answer/6324415

This module performs the following optimizations:
1. Title length optimization
- Truncates the title to 150 characters (products with titles of >150 characters
will be disapproved).
- If titles are truncated from the product description, and the title is < 150
characters, additional info from the description will be appended. This is
expected to improve product performance.

2. Append product fields to the title. This is expected to improve performance.
The following fields are appended if they contain values:
  - gender
  - color
  - sizes
  - brand
"""

import logging
import re
from typing import Any, Dict, List

import constants
from optimizers_abstract import base_optimizer
from util import optimization_util
from util import size_miner

_CHARS_TO_USE_WHEN_CREATING_TITLE: int = 34
_MAX_TITLE_LENGTH: int = 150


class TitleOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that optimizes title."""

  _OPTIMIZER_PARAMETER: str = 'title-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str) -> int:
    """Runs the optimization.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.

    Returns:
      The number of products affected by this optimization.
    """
    num_of_products_optimized = 0

    for entry in product_batch['entries']:
      product = entry['product']
      original_title = product.get('title', '')

      if not original_title:
        original_title = _create_title_from_description(product)
        product['title'] = original_title

      original_title_length = len(original_title)

      _optimize_length_of_title(product)
      self._append_attributes_to_title(product, original_title_length, language,
                                       country)

      if product.get('title', '') != original_title:
        num_of_products_optimized += 1

    return num_of_products_optimized

  def _append_attributes_to_title(self, product: Dict[str, Any],
                                  chars_to_preserve: int, language: str,
                                  country: str) -> None:
    """Appends mined attributes to the title.

    Args:
      product: Product data.
      chars_to_preserve: The num of chars to leave unchanged (used to make sure
        the original title is preserved).
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
    """
    if not self._mined_attributes:
      return

    product_id = product.get('offerId', '')
    size_checker = size_miner.SizeMiner(language, country)
    fields_to_append_to_title = []
    for attribute_name, mined_attribute_values in self._mined_attributes.get(
        product_id, {}).items():
      if attribute_name == 'sizes' and size_checker.is_size_in_attribute(
          product, 'title'):
        # Does not append the size when size information is already in title.
        continue
      if isinstance(mined_attribute_values, str):
        fields_to_append_to_title.append(mined_attribute_values)
      elif isinstance(mined_attribute_values, list):
        fields_to_append_to_title.extend(mined_attribute_values)

    if fields_to_append_to_title:
      base_optimizer.set_optimization_tracking(product,
                                               base_optimizer.OPTIMIZED)
      _append_fields_to_title(product, fields_to_append_to_title,
                              chars_to_preserve)


def _create_title_from_description(product: Dict[str, Any]) -> str:
  """Creates a title from the description field.

  Args:
    product: Product data.

  Returns:
    A title consisting of the first _CHARS_TO_USE_WHEN_CREATING_TITLE from the
    description field + ellipsis, or an empty string if the description field
    does not exist.
  """
  if 'description' in product:
    title =\
      f'{product["description"][:_CHARS_TO_USE_WHEN_CREATING_TITLE].strip()}…'
  else:
    title = ''

  logging.info('Modified item %s: Created title: %s',
               product.get('offerId', ''), title)

  return title


def _optimize_length_of_title(product: Dict[str, Any]) -> None:
  """Optimizes the length of title.

  Args:
    product: Product data.
  """
  _truncate_to_max_length(product)
  _complement_title_with_description(product)


def _truncate_to_max_length(product: Dict[str, Any]) -> None:
  """Truncate the title to the max length: 150.

  This function prevents a product with a 150+ title length from being
  disapproved. Reference: https://support.google.com/merchants/answer/6324415

  Args:
    product: A dictionary containing product data.
  """
  title = product.get('title', '')
  if len(title) > _MAX_TITLE_LENGTH:
    product['title'] = title[:_MAX_TITLE_LENGTH]
    logging.info('Modified item %s: Truncating title: %s',
                 product.get('offerId', ''), product.get('title', ''))
    base_optimizer.set_optimization_tracking(product, base_optimizer.SANITIZED)


def _complement_title_with_description(product: Dict[str, Any]) -> None:
  """Complements title with description if title is truncated from description.

  This is expected to improve ad performance by adding more information to the
  title.

  Args:
    product: Product data.
  """
  title_without_trailing_dots = re.sub('[.…]+$', '', product['title'])
  description = product.get('description', '')
  if title_without_trailing_dots != description and description.startswith(
      title_without_trailing_dots):
    product['title'] = description[:_MAX_TITLE_LENGTH]
    logging.info(
        'Modified item %s: Populating title with description due to detected '
        'title truncation: %s', product['offerId'], product['title'])
    base_optimizer.set_optimization_tracking(product, base_optimizer.OPTIMIZED)


def _append_fields_to_title(product: Dict[str, Any], fields: List[str],
                            chars_to_preserve: int) -> None:
  """Appends the fields to the title.

  Args:
    product: Product data.
    fields: the field values to be appended.
    chars_to_preserve: The num of chars to leave unchanged (used to make sure
      the original title is preserved).
  """
  original_title = product.get('title', '')
  product['title'] = optimization_util.append_keywords_to_field(
      original_title, fields, chars_to_preserve, _MAX_TITLE_LENGTH,
      constants.ALL_ALPHABETIC_CLOTHING_SIZES)

  if product['title'] != original_title:
    logging.info('Modified item %s: Appended field values to title: %s',
                 product['offerId'], product['title'])
