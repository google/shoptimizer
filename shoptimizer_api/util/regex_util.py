# coding=utf-8
# Copyright 2025 Google LLC.
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

"""Module containing helper functions for generating regex.

Used when there is a need to see if a word or a couple of words are present in
another string regarless of spaces.
So if you want to see if "広尾モバイル" is present in another string like
"広尾 モバイル 格安SIM"
You might have a list of these words to check and this is where these methods
will become handy.
By using regex, we can check for matches without having to transform every title
with strip().
"""
import re

# Ignores 0+ whitespace or full-width space characters.
_WHITESPACE_REGEX = '(\s|　)*'  


def convert_to_regex_str_that_ignores_spaces(term: str) -> str:
  r"""Converts a string into a string that can be matched regardless of spacing.

  For example:
  term = 'WWW'
  returns = 'W(\s| )*W(\s| )*W'
  This can be used to match WWW, W W W, WW W, etc.
  This is primarily useful for Asian-language query data.

  Args:
    term: The string to convert into a regex.

  Returns:
    The term converted into a regex that can be matched regardless of spacing.
  """
  # Removes half-width spaces
  term_without_whitespace = term.replace(' ', '')

  # Removes full-width spaces
  term_without_whitespace = term_without_whitespace.replace('　', '')

  # Adds whitespace-ignoring regex to each char.
  regex_term = [char + _WHITESPACE_REGEX for char in term_without_whitespace]

  # Converts the list of chars back to a string and removes last regex.
  regex_term = ''.join(regex_term)[:-len(_WHITESPACE_REGEX)]

  return re.compile(regex_term)


def generate_regex_term_dict(terms: list[str]) -> dict[re.Pattern[str], str]:
  r"""Convert the list of terms into a regex to term dictionary.

  The regex matches the terms regardless of whitespace.

  Args:
    terms: List containing the strings representing the terms we want to create
      regex for. Example: "blue sky", "4 roses".

  Returns:
    A Dictionary regex to term where the regex key matches the value term
    regardless of any whitespace. For example the term "WWW" will become a
    dictionary entry 'W(\s| )*W(\s| )*W' <==> 'WWW'
  """
  regex_to_term_dict = {}
  for term in terms:
    regex = convert_to_regex_str_that_ignores_spaces(term)
    regex_to_term_dict[regex] = term

  return regex_to_term_dict
