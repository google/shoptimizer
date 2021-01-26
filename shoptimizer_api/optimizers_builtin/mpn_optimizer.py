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
"""A module for Shoptimizer API that removes invalid MPN values.

Reference: https://support.google.com/merchants/answer/6324482

Invalid MPN values will cause products to be disapproved.
"""
import logging
import string
from typing import Any, Dict

from optimizers_abstract import base_optimizer

INVALID_MPN_VALUES = (
    '',
    '0',
    '00000000',
    '0000000000',
    '0001',
    '1',
    '10',
    '100',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
    'custommade',
    'default',
    'doesnotapply',
    'false',
    'mpn',
    'na',
    'no',
    'none',
    'notapplicable',
    'notavailable',
    'null',
    'true',
    'unknown',
    'yes',
)


class MPNOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that removes invalid product MPN values."""

  _OPTIMIZER_PARAMETER = 'mpn-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    """Runs the optimization.

    Args:
      product_batch:  A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected by this optimization: int
    """
    num_of_products_optimized = 0
    for entry in product_batch['entries']:
      product = entry['product']
      if 'mpn' in product:
        mpn_value = _normalize_mpn(product.get('mpn', ''))
        if mpn_value in INVALID_MPN_VALUES:
          item_id = product.get('offerId')
          logging.info('Modified item %s: Removing invalid MPN [%s]', item_id,
                       mpn_value)
          del product['mpn']
          num_of_products_optimized += 1
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.SANITIZED)
    return num_of_products_optimized


def _normalize_mpn(mpn: Any,
                   charset: str = string.ascii_letters + string.digits) -> str:
  """Returns the provided text in lowercase with chars not in charset removed.

  Examples:
    "100" should return "100"
    "no value" should return "novalue"
    "n/a" should return "na"
    "N/A" should return "na"
    None should return ""

  Args:
    mpn: A value that represents the product's MPN.
    charset: the set of characters to include in the result text

  Returns:
    Input text converted to lowercase and characters not in the charset stripped
    out.
  """
  if not isinstance(mpn, str):
    return ''
  normalized_mpn = ''.join(char for char in mpn if char in charset)
  normalized_mpn = normalized_mpn.lower()
  return normalized_mpn
