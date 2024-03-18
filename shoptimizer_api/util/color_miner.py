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

"""A module that mines color from product data.

This module mines two color types from product data.
- Standard color: Standard color names to be added to title.
- Unique color: Unique color names to be added to color attribute.

References
- Google Merchant Center Help Center:
https://support.google.com/merchants/answer/6324487?hl=en
"""

import logging
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import MeCab
import mecab_ko

import constants
from util import config_parser
from util import gpc_id_to_string_converter
from util import optimization_util

_COLOR_OPTIMIZER_CONFIG_FILE_NAME: str = 'color_optimizer_config_{}'
_COLOR_OPTIMIZER_CONFIG_OVERRIDE_KEY = 'color_optimizer_config_override'
_COLOR_TERMS_CONFIG_KEY: str = 'color_terms'
_GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME: str = 'gpc_string_to_id_mapping_{}'


class ColorMiner(object):
  """A class that mines color from product data."""

  _language: Optional[str] = None
  _color_config: Optional[Dict[str, Any]] = None
  _gpc_id_to_string_converter: Optional[
      gpc_id_to_string_converter.GPCConverter] = None
  _mecab_tagger: Optional[MeCab.Tagger] = None
  _komecab_tagger: Optional[mecab_ko.Tagger] = None

  def __init__(self, language: str) -> None:
    """Initializes ColorMiner.

    Args:
      language: The configured language code.
    """
    super(ColorMiner, self).__init__()
    self._language = language

    self._color_config = config_parser.get_config_contents(
        _COLOR_OPTIMIZER_CONFIG_OVERRIDE_KEY,
        _COLOR_OPTIMIZER_CONFIG_FILE_NAME.format(language))

    self._gpc_id_to_string_converter = gpc_id_to_string_converter.GPCConverter(
        _GPC_STRING_TO_ID_MAPPING_CONFIG_FILE_NAME.format(language))
    if self._language == constants.LANGUAGE_CODE_JA:
      self._setup_mecab()
    if self._language == constants.LANGUAGE_CODE_KO:
      self._setup_komecab()

  def _setup_mecab(self) -> None:
    """Sets up Mecab tagger for language processing.

    MeCab splits a sentence without any separator including Japanese text into
    words.
    """
    cmd = 'echo `mecab-config --dicdir`"/mecab-ipadic-neologd"'
    config_path = subprocess.run(
        cmd, stdout=subprocess.PIPE, shell=True,
        check=True).stdout.decode('utf-8')
    try:
      self._mecab_tagger = MeCab.Tagger(f'-d {config_path}')
    except RuntimeError as error:
      logging.exception('Error during initializing MeCab Tagger: %s', error)

  def _setup_komecab(self) -> None:
    """Sets up mecab_ko object for korean language processing.

    meacb_ko splits sentences according to Korean morphemes.
    """
    try:
      self._komecab_tagger = mecab_ko.Tagger()
    except RuntimeError as error:
      logging.exception('Error during initializing mecab_ko Tagger: %s', error)

  def mine_color(
      self,
      product: Dict[str,
                    Any]) -> Tuple[Optional[List[str]], Optional[List[str]]]:
    """Mines the color from product fields.

    Args:
      product: A dictionary containing product data.

    Returns:
      Mined standard colors and unique colors, or None if no colors could be
      found.
    """
    color_field = product.get('color')
    if color_field:
      return [color_field], [color_field]

    google_product_category = product.get('googleProductCategory', '')
    gpc_string = self._gpc_id_to_string_converter.convert_gpc_id_to_string(
        google_product_category)

    if not optimization_util.is_particular_google_product_category(
        gpc_string,
        constants.GOOGLE_PRODUCT_CATEGORY_APPAREL_ACCESSORIES_KEYWORDS,
        constants.GOOGLE_PRODUCT_CATEGORY_APPAREL_ACCESSORIES_IDS):
      logging.info(
          'Did not attempt to mine color since googleProductCategory is not "Apparel & Accessories"'
      )
      return None, None

    if not self._color_config:
      logging.warning(
          'Did not attempt to mine color since color config could not be '
          'loaded')
      return None, None

    mined_standard_colors, mined_unique_colors = self._mine_color_from_attribute(
        product.get('title', ''))

    if not mined_standard_colors and not mined_unique_colors:
      mined_standard_colors, mined_unique_colors = self._mine_color_from_attribute(
          product.get('description', ''))

    return mined_standard_colors, mined_unique_colors

  def _mine_color_from_attribute(self,
                                 text: str) -> Tuple[List[str], List[str]]:
    """Mines the color from attribute based on the configured language.

    Args:
      text: Text to be inspected.

    Returns:
      Mined standard colors and unique colors, or empty lists if no colors could
      be found.
    """
    if self._language == 'ja':
      return self._mine_color_by_mecab(text)
    if self._language == 'ko':
      return self._mine_color_by_komecab(text)
    return self._mine_color_by_scanning_terms(text)

  def _mine_color_by_scanning_terms(self,
                                    text: str) -> Tuple[List[str], List[str]]:
    """Mines the color by scanning words.

    It will not add a standard color to if an unique color that includes the
    standard color. For example, if a text includes "dark red", "red" is not
    added to the unique color list.

    Args:
      text: Text to be inspected.

    Returns:
      Mined standard colors and unique colors, or empty lists if no colors could
      be found.
    """
    mined_standard_colors = []
    mined_unique_colors = []

    color_mapping = self._color_config[_COLOR_TERMS_CONFIG_KEY]
    text_in_lowercase = text.lower()
    for unique_color in color_mapping.keys():
      unique_color = unique_color.lower()
      if unique_color in text_in_lowercase:
        standard_color = color_mapping.get(unique_color, '').lower()
        mined_standard_colors.append(standard_color)
        mined_unique_colors.append(unique_color)

    return (_clean_up_term_list(mined_standard_colors,
                                constants.MAX_COLOR_COUNT),
            _clean_up_term_list(mined_unique_colors, constants.MAX_COLOR_COUNT))

  def _mine_color_by_mecab(self, text: str) -> Tuple[List[str], List[str]]:
    """Mines the color by using MeCab for language processing.

    Args:
      text: Text to be inspected.

    Returns:
      Mined standard colors and unique colors, or empty lists if no colors could
      be found.
    """
    mined_standard_colors = []
    mined_unique_colors = []
    color_mapping = self._color_config[_COLOR_TERMS_CONFIG_KEY]
    unique_colors = color_mapping.keys()

    node = self._mecab_tagger.parseToNode(text)
    while node:
      surface = node.surface
      if surface in unique_colors:
        mined_unique_colors.append(surface)
        standard_color = color_mapping.get(surface, '').lower()
        if standard_color:
          mined_standard_colors.append(standard_color)
      node = node.next

    return (_clean_up_term_list(mined_standard_colors,
                                constants.MAX_COLOR_COUNT),
            _clean_up_term_list(mined_unique_colors, constants.MAX_COLOR_COUNT))

  def _mine_color_by_komecab(self, text: str) -> Tuple[List[str], List[str]]:
    """Mines the color by using mecab_ko for language processing.

    We obtain part of speech (pos) from tokens obtained from Korean sentences
    by Mecab (Korean ver), and add standard color and unique color depending on
    pos.

    If NNG (General noun), NNP (Proper noun), or NNB (Bound noun)
    belonging to the noun form matches the color of the noun form,
    the existing value is added to the unique color and converted to
    a standard color mapped to the unique color.

    In the case of adjective type (VA or VA+ETM), if a color that modifies a
    noun is input, find the standard color mapped to it and add the color name
    of the noun type to the unique color and standard color.

    In the case of foreign language (SL), it is the same as English.
    In this case, the existing value is added to the unique color and
    converted to a standard color mapped to the unique color.

    Args:
      text: Text to be inspected.

    Returns:
      Mined standard colors and unique colors, or empty lists if no colors could
      be found.
    """
    mined_standard_colors = []
    mined_unique_colors = []
    color_noun_mapping, color_adjective_mapping, color_en_mapping = (
        self._color_config['color_noun_terms'],
        self._color_config['color_adjective_terms'],
        self._color_config['color_en_terms'],
    )
    unique_noun_colors, unique_adjective_colors, unique_en_colors = (
        color_noun_mapping.keys(),
        color_adjective_mapping.keys(),
        color_en_mapping.keys(),
    )

    node = self._komecab_tagger.parseToNode(text)
    while node:
      surface = node.surface
      feature_list = node.feature.split(',')
      pos = feature_list[0]
      inflect = feature_list[7]

      if (
          pos == 'NNG' or pos == 'NNP' or pos == 'NNB'
      ) and surface in unique_noun_colors:
        mined_unique_colors.append(surface)
        standard_color = color_noun_mapping.get(surface, '').lower()
        if standard_color:
          mined_standard_colors.append(standard_color)

      if pos == 'VA+ETM' and inflect != '*':
        surface_va = inflect.split('/')[0]
        if surface_va in unique_adjective_colors:
          standard_color = color_adjective_mapping.get(surface_va, '').lower()
          if standard_color:
            mined_unique_colors.append(standard_color)
            mined_standard_colors.append(standard_color)

      if pos == 'VA' or surface in unique_adjective_colors:
        standard_color = color_adjective_mapping.get(surface, '').lower()
        if standard_color:
          mined_unique_colors.append(standard_color)
          mined_standard_colors.append(standard_color)

      if pos == 'SL' in unique_en_colors:
        mined_unique_colors.append(surface)
        standard_color = color_en_mapping.get(surface, '').lower()
        if standard_color:
          mined_standard_colors.append(standard_color)

      node = node.next

    return (
        _clean_up_term_list(mined_standard_colors, constants.MAX_COLOR_COUNT),
        _clean_up_term_list(mined_unique_colors, constants.MAX_COLOR_COUNT),
    )


def _clean_up_term_list(term_list: List[str], max_count: int) -> List[str]:
  """Cleans up a list of terms.

  This function removes duplicate elements and returns a list of title-formed
  terms. It also removes colors that would cause the length limit exceed.

  Args:
    term_list: A list of terms.
    max_count: The maximum number of terms returned.

  Returns:
    A list of title-formed terms.
  """
  clean_list = list(dict.fromkeys(term_list))
  clean_list = optimization_util.cut_list_elements_over_max_length(
      clean_list, constants.MAX_COLOR_STR_LENGTH_FOR_EACH)
  clean_list = optimization_util.cut_list_to_limit_concatenated_str_length(
      clean_list, '/', constants.MAX_COLOR_STR_LENGTH_IN_TOTAL)
  clean_list = [term.title() for term in clean_list]
  return optimization_util.cut_list_to_limit_list_length(clean_list, max_count)
