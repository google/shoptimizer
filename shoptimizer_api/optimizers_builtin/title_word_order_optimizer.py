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
from typing import Any, Dict, List

from flask import current_app

import constants
from optimizers_abstract import base_optimizer

_MAX_TITLE_LENGTH = 150

_GCP_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME: str = 'gpc_string_to_id_mapping_{}'
_TITLE_WORD_ORDER_CONFIG_FILE_NAME: str = 'title_word_order_config_{}'


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
        _GCP_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME.format(language), {})
    title_word_order_config = current_app.config.get('CONFIGS', {}).get(
        _TITLE_WORD_ORDER_CONFIG_FILE_NAME.format(language), {})

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
        list_of_split_words_from_title = _generate_list_of_split_words(
            original_title, language)
        keywords_removed_title = original_title
        performance_keywords_to_prepend = []

        for keyword_dict in sorted_keywords_for_gpc:
          title_word_order_config_keyword = keyword_dict.get('keyword', '')

          if len(title_word_order_config_keyword) <= 1:
            continue

          if title_word_order_config_keyword in list_of_split_words_from_title:
            keywords_removed_title = keywords_removed_title.replace(
                title_word_order_config_keyword, '')
            performance_keywords_to_prepend.append(
                f'[{title_word_order_config_keyword}]')
            if len(performance_keywords_to_prepend) >= 3:
              break

        optimized_title = _generate_prepended_title(
            performance_keywords_to_prepend, original_title)

        if len(optimized_title) > _MAX_TITLE_LENGTH:
          optimized_title = _generate_prepended_title(
              performance_keywords_to_prepend, keywords_removed_title)

        product['title'] = optimized_title

      if product.get('title', '') != original_title:
        logging.info(
            'Modified item %s: Moved high-performing keywords to front of title: %s',
            product['offerId'], product['title'])
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.OPTIMIZED)

    return num_of_products_optimized


def _generate_list_of_split_words(text: str, language: str) -> List[str]:
  """Splits text into individual words using the correct method for the given language.

  Args:
    text: Text to be split.
    language: The configured language code.

  Returns:
    The text tokenized into a list of words.
  """
  if language == constants.LANGUAGE_CODE_JA:
    return _split_words_in_japanese(text)
  else:
    return text.split()


def _split_words_in_japanese(text: str) -> List[str]:
  """Splits Japanese text into words by using MeCab.

  Args:
    text: Text to be split.

  Returns:
    The text tokenized into a list of semantically delineated words.
  """
  mecab_tagger = current_app.config.get('MECAB')
  if not mecab_tagger:
    logging.warning('Did not parse title because MeCab was not set up.')
    return []
  node = mecab_tagger.parseToNode(text)
  split_words = []
  while node:
    split_words.append(node.surface)
    node = node.next
  return split_words


def _generate_prepended_title(performance_keywords_to_prepend: List[str],
                              title: str) -> str:
  """Prepends keywords to the title.

  Args:
    performance_keywords_to_prepend: keywords to prepend to the title.
    title: the original title.

  Returns:
    The title with keywords prepended to it.
  """
  prepended_title = f'{"".join(performance_keywords_to_prepend)} {title}'
  return ' '.join(prepended_title.split())
