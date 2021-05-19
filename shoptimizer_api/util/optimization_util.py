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

"""Utility module for optimization."""
import copy
from typing import Any, Collection, Dict, Iterable, List, Sequence

# Amount of space to leave between product data and appended attributes
_SEPARATOR_LENGTH = len(' ')


def optimization_exclusion_specified(entry: Dict[str, Any],
                                     optimizer_parameter: str) -> bool:
  """Returns true if the optimizer exclusion attribute was set and matches the given optimizer parameter."""
  return (entry.get('excludeOptimizers') and
          isinstance(entry.get('excludeOptimizers'), list) and
          optimizer_parameter in entry.get('excludeOptimizers'))


def cut_list_to_limit_list_length(target_list: Sequence[Any],
                                  max_length: int) -> Sequence[Any]:
  """Cuts a list to the max length, returning the result."""
  return target_list[:max_length]


def cut_list_to_limit_concatenated_str_length(
    target_list: Sequence[str], separator: str,
    max_total_str_length: int) -> List[str]:
  """Removes the last items from the list to limit the length of concatenated string of the items.

  For example, when target_list = ['Hello', 'Shoptimizer'] and separator = ',',
  the concatenated string is 'Hello,Shoptimizer' and the length of the string is
  17. If max_total_str_length = 10, the length exceeds the maximum. So, this
  function removes the last item and returns transformed list: ['Hello'].

  Args:
    target_list: A list to be cut.
    separator: Characters used as separator when concatenating the items in the
      list.
    max_total_str_length: The maximum length of the concatenated string.

  Returns:
    A list cut from target_list.
  """
  output_list = list(copy.deepcopy(target_list))
  # Concatenated string length > max str length.
  while len(separator.join(output_list)) > max_total_str_length:
    output_list.pop()
  return output_list


def cut_list_elements_over_max_length(target_list: Sequence[str],
                                      max_length: int) -> List[str]:
  """Removes elements from a list that are over a certain length."""
  return [element for element in target_list if len(element) <= max_length]


def append_keywords_to_field(
    target_field: str,
    keywords: Sequence[str],
    chars_to_preserve: int,
    max_length: int,
    allowlist: Collection[str] = ()) -> str:
  """Appends keywords to the target field.

  If necessary, this function removes the final characters of the target field
  up to chars_to_preserve to make room for keywords. If a keyword is already in
  the target field, it is not appended.

  Args:
    target_field: The field to be transformed.
    keywords: keywords that are appended to the target field.
    chars_to_preserve: The number of original chars to preserve from the start
      of the string to make sure these chars are not removed when appending
      keywords. E.g., use to preserve original title.
    max_length (object): The maximum limit of the field length.
    allowlist: Allowlist of words that are appended even when they are already
      in the target field.

  Returns:
    The target field with keywords appended to the back.
  """
  lowercase_target_field = target_field.lower()
  # An ellipsis and space will be appended before keywords are appended, so
  # subtract the length of 2 separators.
  space_left_to_append_keywords = (max_length - chars_to_preserve) - (
      _SEPARATOR_LENGTH * 2)

  keywords_text = _get_keywords_text(keywords, lowercase_target_field,
                                     space_left_to_append_keywords, allowlist)

  if not keywords_text:
    return target_field

  # Checks if enough whitespace available, and if so appends keywords using
  # whitespace.
  if max_length - len(target_field) >= len(keywords_text):
    field_with_keywords_appended = target_field.strip() + keywords_text
  else:
    # If not enough whitespace is available, trims some chars to make space
    # to append the keywords text.
    insert_pos = _calculate_keywords_insert_pos(target_field, keywords_text,
                                                max_length, chars_to_preserve)
    field_with_keywords_appended = target_field[:insert_pos].strip(
    ) + keywords_text

  return field_with_keywords_appended.strip()


def _get_keywords_text(
    keywords: Sequence[str],
    lowercase_target_field: str,
    space_left_to_append_keywords: int,
    allowlist: Collection[str] = ()) -> str:
  """Generates a string of keywords to be appended to the target field.

  Args:
    keywords: keywords to be appended to the target field.
    lowercase_target_field: The field to append keywords to.
    space_left_to_append_keywords: The space left in the target field to append
      keywords to.
    allowlist: Allowlist of words that are appended even when they are already
      in the target field.

  Returns:
    A string consisting of an ellipsis, space, and space-separated keywords,
    or an empty string if no keywords could be appended.
  """
  keywords_not_in_field = []

  for keyword in keywords:
    if (keyword in allowlist or
        keyword.lower() not in lowercase_target_field) and (
            len(keyword) + _SEPARATOR_LENGTH) <= space_left_to_append_keywords:
      keywords_not_in_field.append(keyword)
      space_left_to_append_keywords -= len(keyword) + _SEPARATOR_LENGTH
      if space_left_to_append_keywords <= 0:
        break

  if not keywords_not_in_field:
    return ''
  elif lowercase_target_field:
    return '… ' + ' '.join(keywords_not_in_field)
  else:
    return ' '.join(keywords_not_in_field)


def _calculate_keywords_insert_pos(target_field: str, keywords_text: str,
                                   max_length: int,
                                   chars_to_preserve: int) -> int:
  """Calculates the position to insert the keywords text in the target field.

  Args:
    target_field: The field to be transformed.
    keywords_text: A string containing a list of keywords to append to the
      target field.
    max_length: The max length of the target field.
    chars_to_preserve: The number of chars to preserve in the target field.

  Returns:
    The position in the target field to insert the keywords text.
  """
  # Calculates the num of chars the target field and keywords text overflows by.
  # E.g. | Title (10) | Desc (20) | Keywords text (10) | = 40 chars
  #       If max_length is 30 chars, then the overflow is 10 chars.
  #       Therefore, the keywords text should be inserted 10 chars to the left
  #       of the target field.
  overflowing_chars = (len(target_field) + len(keywords_text)) - max_length
  insert_pos = len(target_field) - overflowing_chars

  # Truncating a digit (1.5, 600, etc.) can lead to inaccurate product
  # information, so we need to decrement the insert position until we hit a
  # non-digit character, or the start of chars_to_preserve.
  # (chars_to_preserve usually represents the original product title.)
  while (target_field[insert_pos] == '.' or
         target_field[insert_pos].isdigit()) and insert_pos > chars_to_preserve:
    insert_pos -= 1

  return insert_pos


def is_particular_google_product_category(given_category: str,
                                          category_keywords: Iterable[str],
                                          category_ids: Iterable[str]) -> bool:
  """Checks if a given google_product_category value is in a set of particular google_product_category values.

  Args:
    given_category: google_product_category value to be checked.
    category_keywords: Keywords that are in the target google_product_category.
    category_ids: Target google_product_category IDs.

  Returns:
    Whether a given value is the particular google_product_category or not.
  """
  for category_word in category_keywords:
    if category_word in given_category:
      return True

  if given_category in category_ids:
    return True

  return False
