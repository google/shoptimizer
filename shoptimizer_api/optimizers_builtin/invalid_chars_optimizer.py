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
"""A module for Shoptimizer API that removes invalid characters from the title and description.

Reference: https://support.google.com/merchants/answer/160079

If the title contains an invalid char, the whole product will be disapproved.
If the description contains an invalid char, the description will be rejected.

Although Merchant Center supports UTF-8/16 encoding, code points in the
Unicode private use area (0xE000-0xF8FF) are not valid and any field that
contains these characters will be rejected.

This optimizer finds characters with a code point that maps to the private
use area and removes them.
"""
import logging
from typing import Any, Dict, List

from optimizers_abstract import base_optimizer

_FIELDS_TO_SANITIZE = ['description', 'title']
# Can be changed to a space etc. if you want to replace invalid chars instead of
# removing them.
_REPLACEMENT_CHAR: str = ''
_UNICODE_PRIVATE_USE_AREA_START = 0xE000
_UNICODE_PRIVATE_USE_AREA_END = 0xF8FF


class InvalidCharsOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that removes invalid chars from the title and description."""

  _OPTIMIZER_PARAMETER = 'invalid-chars-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    """Runs the optimization.

    Removes invalid chars from the title and description.
    See above for the definition of an invalid char.

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

      product_was_sanitized = _sanitize_fields(product, _FIELDS_TO_SANITIZE)

      if product_was_sanitized:
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.SANITIZED)
    return num_of_products_optimized


def _sanitize_fields(product: Dict[str, Any], fields: List[str]) -> bool:
  """Removes invalid chars from product fields.

  Invalid chars are any chars that have code points in the Unicode private use
  area (0xE000-0xF8FF).

  Args:
    product: Product data.
    fields: A list of product fields to sanitize.

  Returns:
    True if any field was sanitized, False otherwise.
  """
  field_was_sanitized = False

  for field in fields:
    field_chars = list(product.get(field, ''))

    if not field_chars:
      continue

    for index, char in enumerate(field_chars):
      code_point = ord(char)
      if _UNICODE_PRIVATE_USE_AREA_START <= code_point <= _UNICODE_PRIVATE_USE_AREA_END:
        logging.info('Modified item %s: Removing invalid char [%s] from [%s]',
                     product.get('offerId', ''), code_point, field)
        field_chars[index] = _REPLACEMENT_CHAR
        field_was_sanitized = True

    product[field] = ''.join(field_chars)

  return field_was_sanitized
