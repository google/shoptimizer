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

This module loads configurations below from file:
shoptimizer_api/config/title_word_order_options.json.
- descriptionIncluded: Finding keywords in description if true.
- productTypesIncluded: Finding keywords in productTypes if true.
- optimizationLevel: allowed values are "standard" and "aggressive".
  When set to "standard" we apply our high performing keywords title
  optimizations to products with google product category level 3 only.
  When set to "aggressive we apply our high performing keywords title
  optimizations to products with google product category level 3, 4 or more.
"""

import enum
import logging
from typing import Any, Dict, List, Optional, Text, Tuple, Union
from util import promo_text_remover as promo_text_remover_lib
from util import app_util
from flask import current_app

import constants

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import optimization_util

_TITLE_CHARS_VISIBLE_TO_USER_EN = 25
_TITLE_CHARS_VISIBLE_TO_USER_JA = 12
_MAX_KEYWORDS_PER_TITLE = 3
_MAX_TITLE_LENGTH = 150

_GCP_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME: str = 'gpc_string_to_id_mapping_{}'
_TITLE_WORD_ORDER_CONFIG_FILE_NAME: str = 'title_word_order_config_{}'
_TITLE_WORD_ORDER_BLOCKLIST_FILE_NAME: str = 'title_word_order_blocklist_{}'
_TITLE_WORD_ORDER_OPTIONS_FILE_NAME: str = 'title_word_order_options'

# The following constants must be set if Shoptimizer is used outside
# a Flask context.
GPC_STRING_TO_ID_MAPPING_CONFIG = None
TITLE_WORD_ORDER_CONFIG = None
BLOCKLIST_CONFIG = None
TITLE_WORD_ORDER_OPTIONS_CONFIG = None


def _get_required_configs():
  """Gets a map of required configs."""
  return {
      'gpc_string_to_id_mapping_config': GPC_STRING_TO_ID_MAPPING_CONFIG,
      'title_word_order_config': TITLE_WORD_ORDER_CONFIG,
      'blocklist_config': BLOCKLIST_CONFIG,
      'title_word_order_options_config': TITLE_WORD_ORDER_OPTIONS_CONFIG,
  }


def _get_configs_from_environment(language: str):
  """Gets optimizer configs from the local environment."""
  if current_app:
    # It is running on Flask.
    gpc_string_to_id_mapping = (
        current_app.config.get('CONFIGS', {}).get(
            _GCP_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME.format(language), {}))

    title_word_order_config = (
        current_app.config.get('CONFIGS', {}).get(
            _TITLE_WORD_ORDER_CONFIG_FILE_NAME.format(language), {}))

    blocklist_config = (
        current_app.config.get('CONFIGS', {}).get(
            _TITLE_WORD_ORDER_BLOCKLIST_FILE_NAME.format(language), {}))

    title_word_order_options = (
        current_app.config.get(
            'CONFIGS', {}).get(_TITLE_WORD_ORDER_OPTIONS_FILE_NAME))

    return (
        gpc_string_to_id_mapping,
        title_word_order_config,
        blocklist_config,
        title_word_order_options)
  else:
    # It is not running on Flask.
    #
    # Checks all required configs are set.
    for config_name, config_value in _get_required_configs().items():
      if config_value is None:
        raise RuntimeError(
            'Config `%s` must be set in order to use this optimizer' %
            config_name)

    return (
        GPC_STRING_TO_ID_MAPPING_CONFIG,
        TITLE_WORD_ORDER_CONFIG,
        BLOCKLIST_CONFIG,
        TITLE_WORD_ORDER_OPTIONS_CONFIG)


class _OptimizationLevel(enum.Enum):
  """Enums for optimization level."""
  AGGRESSIVE = 'aggressive'
  STANDARD = 'standard'


class TitleWordOrderOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer that optimizes title word order."""

  _OPTIMIZER_PARAMETER = 'title-word-order-optimizer'
  _title_word_order_options = {}

  def _optimize(
      self, product_batch: Dict[str, Any], language: str, country: str,
      currency: str) -> optimization_result_counts.OptimizationResultCounts:
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
    num_of_products_optimized = 0
    num_of_products_excluded = 0

    (gpc_string_to_id_mapping,
     title_word_order_config,
     blocklist_config,
     title_word_order_options) = _get_configs_from_environment(language)

    self._title_word_order_options = title_word_order_options

    keyword_blocklist = (
        [keyword.lower() for keyword in blocklist_config])

    optimization_includes_description = (
        self._optimization_includes_description())
    optimization_includes_product_types = (
        self._optimization_includes_product_types())

    promo_text_remover = promo_text_remover_lib.PromoTextRemover(
        language=language)

    optimization_level = self._get_optimization_level()

    for entry in product_batch['entries']:

      if (optimization_util.optimization_exclusion_specified(
          entry, self._OPTIMIZER_PARAMETER)):
        num_of_products_excluded += 1
        continue

      product = entry['product']
      original_title = product.get('title', None)
      description = product.get('description', None)
      product_types = product.get('productTypes', [])
      gpc = product.get('googleProductCategory', '')

      if not original_title:
        continue

      # Get the string version of the GPC if it was provided as a number ID.
      if isinstance(gpc, int) or gpc.isdigit():
        gpc_string = get_gpc_as_string(gpc, gpc_string_to_id_mapping)
        if not gpc_string:
          continue
      else:
        gpc_string = gpc

      if _should_skip_optimization(gpc_string, optimization_level):
        continue

      gpc_id = _get_level_3_gpc_id(gpc_string, gpc_string_to_id_mapping)

      if not gpc_id:
        continue

      keywords_for_gpc = title_word_order_config.get(str(gpc_id), [])
      allowed_keywords_for_gpc = _remove_keywords_in_blocklist(
          keywords_for_gpc, keyword_blocklist)
      allowed_keywords_for_gpc = _remove_keywords_with_promo(
          promo_text_remover, allowed_keywords_for_gpc)
      sorted_keywords_for_gpc = _sort_keywords_for_gpc_by_descending_weight(
          allowed_keywords_for_gpc)

      title_to_process = original_title
      title_words = _tokenize_text(title_to_process, language)
      description_words = _tokenize_text(
          description, language) if optimization_includes_description else []
      joined_product_types = ' '.join(product_types)
      product_types_words = _tokenize_text(
          joined_product_types,
          language) if optimization_includes_product_types else []

      (keywords_visible_to_user, keywords_not_visible_to_user,
       title_without_keywords) = (
           _generate_front_and_back_keyword_lists(sorted_keywords_for_gpc,
                                                  title_to_process, title_words,
                                                  description_words,
                                                  product_types_words,
                                                  language))

      keywords_to_prepend = _generate_list_of_keywords_to_prepend(
          keywords_visible_to_user, keywords_not_visible_to_user,
          title_to_process, language)
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

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)

  def _get_optimization_level(self) -> _OptimizationLevel:
    """Returns configured optimization level."""
    if self._title_word_order_options.get(
        'optimizationLevel').lower() == _OptimizationLevel.AGGRESSIVE.value:
      return _OptimizationLevel.AGGRESSIVE
    else:
      return _OptimizationLevel.STANDARD

  def _optimization_includes_description(self) -> bool:
    """Returns whether description field should be inspected or not when finding keywords."""
    return self._title_word_order_options.get('descriptionIncluded', False)

  def _optimization_includes_product_types(self) -> bool:
    """Returns whether productTypes field should be inspected or not when finding keywords."""
    return self._title_word_order_options.get('productTypesIncluded', False)


def _should_skip_optimization(gpc_string: str,
                              optimization_level: _OptimizationLevel) -> bool:
  """Returns whether the product should skip the optimization.

  With optimization_level "aggressive", the optimization is always be applied.
  With optimization_level "standard", the optimization is skipped when the level
  of Google Product Category is deeper than 3.

  Args:
    gpc_string: Google Product Category in string format.
    optimization_level: Configured optimization level.

  Returns:
    Whether the product should skip the optimization.
  """
  if optimization_level == _OptimizationLevel.AGGRESSIVE:
    return False
  else:
    gpc_list = gpc_string.split('>')
    # 3 because Mizuyokan config file only contains analysis for GPC
    # level 1,2 and 3
    return len(gpc_list) > 3


def _get_level_3_gpc_id(
    gpc_string: str,
    gpc_string_to_id_mapping: Dict[str, Any],
) -> int:
  """Gets the GPC ID for the given product with a GPC in string format.

  Args:
    gpc_string: Google Product Category in string format.
    gpc_string_to_id_mapping: The list of gpc mappings from the config file.

  Returns:
    A GPC ID that this product's GPC maps to, if it was found.
  """
  gpc_list = gpc_string.split('>')
  gpc_three_levels = '>'.join(gpc_list[:3]).strip()
  return gpc_string_to_id_mapping.get(gpc_three_levels)


def _sort_keywords_for_gpc_by_descending_weight(
    keywords_for_gpc: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """Sorts keywords_for_gpc by their weight values in descending order."""
  return sorted(keywords_for_gpc, key=lambda x: x['weight'], reverse=True)


def _remove_keywords_in_blocklist(
    keywords: List[Dict[str, Any]],
    keyword_blocklist: List[str]) -> List[Dict[str, Any]]:
  """Removes keywords from the keyword list that were found in the blocklist.

  The check for existence is case-insensitive.

  Args:
    keywords: List of dictionaries of keywords and weights.
    keyword_blocklist: Blocklist of keywords in the config file. The keywords
      must be lower case.

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
  if current_app:
    mecab_tagger = current_app.config.get('MECAB')
  else:
    mecab_tagger = app_util.setup_mecab()

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
    product_types_words: List[str],
    language: str) -> Tuple[List[str], List[str], str]:
  """Generates two lists of keywords: those in the front and back of the title.

  Args:
    sorted_keywords: A list of dictionaries of keywords and weights, sorted by
      descending weight.
    title_to_process: The product title being optimized.
    title_words: A list of semantically tokenized words in the title.
    description_words: A list of semantically tokenized description words.
    product_types_words: A list of semantically tokenized product types words.
    language: The configured language code.

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
      if language == constants.LANGUAGE_CODE_JA:
        user_visible_text = title_to_process[:_TITLE_CHARS_VISIBLE_TO_USER_JA]
      else:
        user_visible_text = title_to_process[:_TITLE_CHARS_VISIBLE_TO_USER_EN]
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
    keywords_not_visible_to_user: List[str], title: str,
    language: str) -> List[str]:
  """Determines which performant keywords need to be prepended and sorts them.

  Args:
    keywords_visible_to_user: keywords that were found near the front of the
      given title.
    keywords_not_visible_to_user: keywords that were not found near the front of
      the given title.
    title: the title to append performant keywords to.
    language: The configured language code.

  Returns:
    A list of high-performing keywords.
  """
  keywords_to_be_prepended = keywords_not_visible_to_user
  for skipped_keyword in keywords_visible_to_user:
    temp_prepended_title = _generate_prepended_title(keywords_to_be_prepended,
                                                     title)
    if language == constants.LANGUAGE_CODE_JA:
      front_of_title = temp_prepended_title[:_TITLE_CHARS_VISIBLE_TO_USER_JA]
    else:
      front_of_title = temp_prepended_title[:_TITLE_CHARS_VISIBLE_TO_USER_EN]

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


def get_gpc_as_string(
    gpc: Union[Text, int],
    gpc_string_to_id_mapping: Dict[str, int]) -> Optional[Text]:
  """Returns the text representation of a gpc, or '' if it isn't found."""
  gpc_string = ''
  for key, value in gpc_string_to_id_mapping.items():
    if value == int(gpc):
      gpc_string = key
  return gpc_string


def _remove_keywords_with_promo(
    promo_text_remover: promo_text_remover_lib,
    keywords_for_gpc: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """Remove elements of keywords_for_gpc that contains promo text as keyword.

  Args:
    promo_text_remover: a promo_text_remover object.
    keywords_for_gpc:  A list of dictionaries of keywords and weights.

  Returns:
    A list of dictionaries of keywords and weights where the keywords does not
    contain promo text.
  """
  keywords_with_promo = [x.get('keyword') for x in keywords_for_gpc]
  keywords_without_promo = promo_text_remover.remove_keywords_with_promo(
      keywords_with_promo)
  return [
      x for x in keywords_for_gpc if x.get('keyword') in keywords_without_promo
  ]
