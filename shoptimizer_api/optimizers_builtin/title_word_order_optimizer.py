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

"""A module for Shoptimizer API that optimizes title values.

This module performs the following optimization:
1. Detects high-performing words.
2. Moves the high-performing words to the front of the title.
"""

import logging
from typing import Any, Dict

from flask import current_app

from optimizers_abstract import base_optimizer


class TitleWordOrderOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that optimizes title word order."""

  _OPTIMIZER_PARAMETER = 'title-word-order-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    """Runs the optimization.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected by this optimization.
    """
    gpc_id_to_string_mapping = current_app.config.get('CONFIGS', {}).get(
        f'gpc_id_to_string_mapping_{language}', {})
    title_word_order_config = current_app.config.get('CONFIGS', {}).get(
        f'title_word_order_config_{language}', {})

    num_of_products_optimized = 0

    for entry in product_batch['entries']:
      product = entry['product']
      original_title = product.get('title', None)

      if original_title is None or not original_title:
        break

      google_product_category = product.get('googleProductCategory', '')

      google_product_category_list = google_product_category.split('>')
      google_product_category_3_levels = '>'.join(
          google_product_category_list[:3]).strip()

      google_product_category_id = gpc_id_to_string_mapping.get(
          google_product_category_3_levels)

      if google_product_category_id is not None and google_product_category_id:

        keywords_for_gpc = title_word_order_config.get(
            str(google_product_category_id), [])
        sorted_keywords_for_gpc = sorted(
            keywords_for_gpc, key=lambda x: x['weight'], reverse=True)
        performance_keywords_to_prepend = []
        title_to_transform = original_title
        for keyword_dict in sorted_keywords_for_gpc:
          keyword = keyword_dict.get('keyword')
          if keyword in title_to_transform:
            title_to_transform = title_to_transform.replace(keyword, '')
            performance_keywords_to_prepend.append(keyword)
            if len(performance_keywords_to_prepend) >= 3:
              break

        optimized_title = (f'{" ".join(performance_keywords_to_prepend)} '
                           f'{title_to_transform}')
        normalized_whitespace_title = ' '.join(optimized_title.split())
        product['title'] = normalized_whitespace_title

      if product.get('title', '') != original_title:
        logging.info(
            'Modified item %s: Moved high-performing keywords to front of title: %s',
            product['offerId'], product['title'])
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.OPTIMIZED)

    return num_of_products_optimized
