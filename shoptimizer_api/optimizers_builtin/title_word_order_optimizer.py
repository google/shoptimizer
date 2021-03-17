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
from typing import Any, Dict, List, Tuple

from flask import current_app

import constants
from optimizers_abstract import base_optimizer

_TITLE_CHARS_VISIBLE_TO_USER = 25
_MAX_KEYWORDS_PER_TITLE = 3
_MAX_TITLE_LENGTH = 150

_GCP_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME: str = 'gpc_string_to_id_mapping_{}'
_TITLE_WORD_ORDER_CONFIG_FILE_NAME: str = 'title_word_order_config_{}'
_TITLE_WORD_ORDER_BLOCKLIST_FILE_NAME: str = 'title_word_order_blocklist_{}'


class TitleWordOrderOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that optimizes title word order."""

  _OPTIMIZER_PARAMETER = 'title-word-order-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    """Runs the optimization.

    This is called by process() in the base class.

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected by this optimization.
    """
    gpc_string_to_id_mapping = current_app.config.get('CONFIGS', {}).get(
        _GCP_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME.format(language), {})
    title_word_order_config = current_app.config.get('CONFIGS', {}).get(
        _TITLE_WORD_ORDER_CONFIG_FILE_NAME.format(language), {})
    blocklist_config = current_app.config.get('CONFIGS', {}).get(
        _TITLE_WORD_ORDER_BLOCKLIST_FILE_NAME.format(language), {})
    keyword_blocklist = [keyword.lower() for keyword in blocklist_config]

    num_of_products_optimized = 0

    for entry in product_batch['entries']:
      product = entry['product']
      original_title = product.get('title', None)
      description = product.get('description', None)
      product_types = product.get('productTypes', [])

      if not original_title:
        continue

      gpc_id = _get_gpc_id(product, gpc_string_to_id_mapping)

      if not gpc_id:
        continue

      keywords_for_gpc = title_word_order_config.get(str(gpc_id), [])
      sorted_keywords_for_gpc = _sort_keywords_for_gpc_by_descending_weight(
          keywords_for_gpc)
      sorted_keywords_for_gpc = _remove_keywords_in_blocklist(
          sorted_keywords_for_gpc, keyword_blocklist)

      title_to_process = original_title
      title_words = _tokenize_text(title_to_process, language)
      description_words = _tokenize_text(description, language)
      joined_product_types = ' '.join(product_types)
      product_types_words = _tokenize_text(joined_product_types, language)

      (keywords_visible_to_user, keywords_not_visible_to_user,
       title_without_keywords) = (
           _generate_front_and_back_keyword_lists(sorted_keywords_for_gpc,
                                                  title_to_process, title_words,
                                                  description_words,
                                                  product_types_words))

      keywords_to_prepend = _generate_list_of_keywords_to_prepend(
          keywords_visible_to_user, keywords_not_visible_to_user,
          title_to_process)
      ordered_keywords_to_prepend = _reorder_keywords_by_weight(
          keywords_to_prepend, sorted_keywords_for_gpc)

      optimized_title = _generate_prepended_title(ordered_keywords_to_prepend,
                                                  title_to_process)

      if len(optimized_title) > _MAX_TITLE_LENGTH:
        optimized_title = _generate_prepended_title(ordered_keywords_to_prepend,
                                                    title_without_keywords)

      product['title'] = optimized_title

      if product.get('title', '') != original_title:
        logging.info(
            'Modified item %s: Moved high-performing keywords to front of title: %s',
            product['offerId'], product['title'])
        num_of_products_optimized += 1
        base_optimizer.set_optimization_tracking(product,
                                                 base_optimizer.OPTIMIZED)

    return num_of_products_optimized


def _get_gpc_id(product: Dict[str, Any],
                gpc_string_to_id_mapping: Dict[str, Any]) -> int:
  """Gets the GPC ID for the given product with a GPC in string format.

  Args:
    product: The product with a GPC to parse and lookup.
    gpc_string_to_id_mapping: The list of gpc mappings from the config file.

  Returns:
    A GPC ID that this product's GPC maps to, if it was found.
  """
  gpc = product.get('googleProductCategory', '')
  gpc_list = gpc.split('>')
  gpc_three_levels = '>'.join(gpc_list[:3]).strip()
  return gpc_string_to_id_mapping.get(gpc_three_levels)


def _sort_keywords_for_gpc_by_descending_weight(
    keywords_for_gpc: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """Sorts keywords_for_gpc by their weight values in descending order."""
  return sorted(keywords_for_gpc, key=lambda x: x['weight'], reverse=True)


def _remove_keywords_in_blocklist(
    keywords: List[Dict[str, Any]],
    keyword_blocklist: List[str]) -> List[Dict[str, Any]]:
  """Removes keywords in the blocklist from the keyword list.

  The Check of the existence is case-insensitive.

  Args:
    keywords: List of dictionaries of keywords and weights.
    keyword_blocklist: Blocklist of keywords in the config file.

  Returns:
    List of dictionaries of keywords and weights not in the blocklist.
  """
  allowed_keywords = []
  for keyword_weight in keywords:
    if keyword_weight.get('keyword', '').lower() in keyword_blocklist:
      continue
    else:
      allowed_keywords.append(keyword_weight)
  return allowed_keywords


def _tokenize_text(text: str, language: str) -> List[str]:
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


def _generate_front_and_back_keyword_lists(
    sorted_keywords: List[Dict[str, Any]], title_to_process: str,
    title_words: List[str], description_words: List[str],
    product_types_words: List[str]) -> Tuple[List[str], List[str], str]:
  """Generates two lists of keywords: those in the front and back of the title.

  Args:
    sorted_keywords: A list of dictionaries of keywords and weights, sorted by
      descending weight.
    title_to_process: The product title being optimized.
    title_words: A list of semantically tokenized words in the title.
    description_words: A list of semantically tokenized description words.
    product_types_words: A list of semantically tokenized product types words.

  Returns:
    A list of matching keywords near the front of the title, a list of
    matching
    keywords near the back of the title, and a title with the matching
    keywords
    removed.
  """
  keywords_visible_to_user = []
  keywords_not_visible_to_user = []
  title_without_keywords = title_to_process

  # Identify matching keywords in the title and populate separate lists
  # of keywords near the front and keywords not near the front.
  for keyword_and_weight in sorted_keywords:
    try:
      keyword = keyword_and_weight['keyword']
    except KeyError:
      continue

    # Creates a title for "moved" keywords, i.e. keywords removed from the
    # title and added to the front, used in the case of too-long titles.
    if keyword in title_words or keyword in description_words or keyword in product_types_words:
      title_without_keywords = title_without_keywords.replace(keyword, '')
      user_visible_text = title_to_process[:_TITLE_CHARS_VISIBLE_TO_USER]
      if keyword in user_visible_text:
        keywords_visible_to_user.append(keyword)
      else:
        keywords_not_visible_to_user.append(keyword)

      if _num_keywords_to_prepend_meets_or_exceeds_limit(
          keywords_not_visible_to_user):
        break
  return (keywords_visible_to_user, keywords_not_visible_to_user,
          title_without_keywords)


def _num_keywords_to_prepend_meets_or_exceeds_limit(
    keywords_to_prepend: List[str]) -> bool:
  """"Checks if the number of the given list of keywords hit the max allowed."""
  return len(keywords_to_prepend) >= _MAX_KEYWORDS_PER_TITLE


def _generate_list_of_keywords_to_prepend(
    keywords_visible_to_user: List[str],
    keywords_not_visible_to_user: List[str], title: str) -> List[str]:
  """Determines which performant keywords need to be prepended and sorts them.

  Args:
    keywords_visible_to_user: keywords that were found near the front of the
      given title.
    keywords_not_visible_to_user: keywords that were not found near the front of
      the given title.
    title: the title to append performant keywords to.

  Returns:
    A list of high-performing keywords.
  """
  keywords_to_be_prepended = keywords_not_visible_to_user
  for skipped_keyword in keywords_visible_to_user:
    temp_prepended_title = _generate_prepended_title(keywords_to_be_prepended,
                                                     title)
    front_of_title = temp_prepended_title[:_TITLE_CHARS_VISIBLE_TO_USER]

    # The skipped keyword was pushed out too far due to the prepend, so
    # include it in the list of to-be-prepended keywords.
    if skipped_keyword not in front_of_title:
      keywords_to_be_prepended.append(skipped_keyword)
      keywords_visible_to_user.remove(skipped_keyword)

  return keywords_to_be_prepended


def _reorder_keywords_by_weight(
    keywords_to_prepend: List[str],
    sorted_keywords_for_gpc: List[Dict[str, Any]]) -> List[str]:
  """Reorders keywords by weight."""
  sorted_keywords_to_prepend = []
  for weighted_word in sorted_keywords_for_gpc:
    if weighted_word['keyword'] in keywords_to_prepend:
      sorted_keywords_to_prepend.append(weighted_word['keyword'])

  return sorted_keywords_to_prepend


def _generate_prepended_title(performant_keywords_to_prepend: List[str],
                              title: str) -> str:
  """Prepends keywords in square brackets to the title.

  Args:
    performant_keywords_to_prepend: keywords to prepend to the title.
    title: the original title.

  Returns:
    The title with keywords in square brackets prepended to it.
  """

  formatted_keywords = [
      '[' + keyword + ']'
      for keyword in performant_keywords_to_prepend[:_MAX_KEYWORDS_PER_TITLE]
  ]
  prepended_title = f'{"".join(formatted_keywords)} {title}'
  return ' '.join(prepended_title.split())
