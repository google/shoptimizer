# coding=utf-8
# Copyright 2022 Google LLC.
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

"""Tests for regex_util."""

import re

from absl.testing import parameterized
from util import regex_util


class RegexUtilTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'convert_english_term',
          'term': 'E Term',
          'expected_regex': 'E(\\s|　)*T(\\s|　)*e(\\s|　)*r(\\s|　)*m',
      },
      {
          'testcase_name': 'convert_japanese_term',
          'term': '商品',
          'expected_regex': '商(\\s|　)*品',
      },
      {
          'testcase_name': 'empty_string',
          'term': '',
          'expected_regex': '',
      },
  )
  def test_convert_to_regex_str_that_ignores_spaces(self, term, expected_regex):
    actual_regex = regex_util.convert_to_regex_str_that_ignores_spaces(term)
    self.assertEqual(expected_regex, actual_regex.pattern)

  def test_generate_regex_term_dict(self):
    terms = ['E Term', '商品', '']

    actual_regex_to_term = regex_util.generate_regex_term_dict(terms)

    expected_regex_to_term = {
        re.compile('E(\\s|　)*T(\\s|　)*e(\\s|　)*r(\\s|　)*m'): 'E Term',
        re.compile('商(\\s|　)*品'): '商品',
        re.compile(''): ''
    }

    self.assertEqual(expected_regex_to_term, actual_regex_to_term)
