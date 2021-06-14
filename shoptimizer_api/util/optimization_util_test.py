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

"""Unit tests for optimization_utils module."""

import copy

from absl.testing import parameterized

from test_data import requests_bodies
from util import optimization_util

MAX_LIST_LENGTH = 3
MAX_TOTAL_STR_LENGTH = 10
SEPARATOR = ','


class OptimizationUtilTest(parameterized.TestCase):

  def test_cut_list_to_limit_list_length_shorten_list_when_too_long(self):
    target_list = list(range(MAX_LIST_LENGTH + 1))

    actual_output = optimization_util.cut_list_to_limit_list_length(
        target_list, MAX_LIST_LENGTH)

    expected_output = list(range(MAX_LIST_LENGTH))
    self.assertEqual(expected_output, actual_output)
    self.assertLen(actual_output, MAX_LIST_LENGTH)

  @parameterized.named_parameters({
      'testcase_name': 'empty',
      'target_list': []
  }, {
      'testcase_name': 'one element',
      'target_list': [0]
  }, {
      'testcase_name': 'max length',
      'target_list': list(range(MAX_LIST_LENGTH))
  })
  def test_cut_list_to_limit_list_length_not_mutate_list_when_not_too_long(
      self, target_list):
    actual_output = optimization_util.cut_list_to_limit_list_length(
        target_list, MAX_LIST_LENGTH)

    self.assertEqual(target_list, actual_output)
    self.assertLessEqual(len(actual_output), MAX_LIST_LENGTH)

  @parameterized.named_parameters(
      {
          'testcase_name': 'too many elements',
          'target_list': ['a'] * MAX_TOTAL_STR_LENGTH,
          'expected_list': ['a'] * 5
      }, {
          'testcase_name': 'first value is too long',
          'target_list': ['a' * (MAX_TOTAL_STR_LENGTH + 1)],
          'expected_list': []
      })
  def test_cut_list_to_limit_concatenated_str_length_shorten_list_when_too_long(
      self, target_list, expected_list):
    actual_output = optimization_util.cut_list_to_limit_concatenated_str_length(
        target_list, SEPARATOR, MAX_TOTAL_STR_LENGTH)

    self.assertEqual(expected_list, actual_output)

  @parameterized.named_parameters({
      'testcase_name': 'empty',
      'target_list': [],
  }, {
      'testcase_name': 'one short element',
      'target_list': ['a'],
  }, {
      'testcase_name': 'two short elements',
      'target_list': ['a', 'a'],
  }, {
      'testcase_name': 'equal to max',
      'target_list': ['a', 'a', 'a', 'a', 'aa'],
  })
  def test_cut_list_to_limit_concatenated_str_length_not_mutate_list_when_not_too_long(
      self, target_list):
    original_list = copy.deepcopy(target_list)

    actual_output = optimization_util.cut_list_to_limit_concatenated_str_length(
        target_list, SEPARATOR, MAX_TOTAL_STR_LENGTH)

    self.assertEqual(original_list, actual_output)

  @parameterized.named_parameters(
      {
          'testcase_name': 'one keyword',
          'keywords': ['a'],
          'expected_output': 'dummy field… a'
      }, {
          'testcase_name': 'two keywords',
          'keywords': ['a', 'b'],
          'expected_output': 'dummy field… a b'
      })
  def test_append_keywords_to_field_append_keywords_when_length_under_max(
      self, keywords, expected_output):
    target_field = 'dummy field'

    actual_output = optimization_util.append_keywords_to_field(
        target_field, keywords, 0, 100)

    self.assertEqual(expected_output, actual_output)

  @parameterized.named_parameters(
      {
          'testcase_name': 'one keyword',
          'keywords': ['a'],
          'expected_output': 'dummy fi… a'
      }, {
          'testcase_name': 'two keywords',
          'keywords': ['a', 'b'],
          'expected_output': 'dummy… a b'
      })
  def test_append_keywords_to_field_append_keywords_after_removing_last_characters_when_length_exceeds_max(
      self, keywords, expected_output):
    target_field = 'dummy field'

    actual_output = optimization_util.append_keywords_to_field(
        target_field, keywords, 0, len(target_field))

    self.assertEqual(expected_output, actual_output)

  def test_append_keywords_to_field_not_append_when_keywords_empty(self):
    target_field = 'dummy field'

    actual_output = optimization_util.append_keywords_to_field(
        target_field, [], 0, len(target_field))

    self.assertEqual(target_field, actual_output)

  @parameterized.named_parameters(
      {
          'testcase_name': 'one keyword already in field',
          'keywords': ['dummy'],
          'expected_output': 'dummy field'
      }, {
          'testcase_name': 'one keyword already in field and one not there',
          'keywords': ['dummy', 'new'],
          'expected_output': 'dummy… new'
      })
  def test_append_keywords_to_field_not_append_when_keywords_already_there(
      self, keywords, expected_output):
    target_field = 'dummy field'

    actual_output = optimization_util.append_keywords_to_field(
        target_field, keywords, 0, len(target_field))

    self.assertEqual(expected_output, actual_output)

  def test_append_keywords_to_field_appends_when_keyword_is_in_allowlist_and_is_in_the_field(
      self):
    target_field = 'dummy field'

    actual_output = optimization_util.append_keywords_to_field(
        target_field, ['M'], 0, 100, allowlist=['M'])

    self.assertEqual('dummy field… M', actual_output)

  def test_append_keywords_to_field_does_not_append_when_no_space_to_append(
      self):
    original_field = 'dummy field'
    keywords = ['keyword1', 'keyword2']
    chars_to_preserve = len(original_field)

    actual_output = optimization_util.append_keywords_to_field(
        original_field, keywords, chars_to_preserve, len(original_field))

    self.assertEqual(original_field, actual_output)

  def test_append_keywords_to_field_only_appends_fields_that_will_fit(self):
    original_field = 'dummy field'
    field_to_append = 'Field to append'
    field_that_is_too_long_to_append = ('Super long field that does not have'
                                        'space to be appended')
    keywords = [field_that_is_too_long_to_append, field_to_append]
    chars_to_preserve = len(original_field)
    max_len = len(original_field) + 20
    expected_field = f'{original_field}… {field_to_append}'

    actual_output = optimization_util.append_keywords_to_field(
        original_field, keywords, chars_to_preserve, max_len)

    self.assertEqual(expected_field, actual_output)

  def test_append_keywords_to_field_does_not_truncate_description_if_field_can_fit_in_whitespace(
      self):
    original_field = 'dummy field'
    field_to_append = 'Field to append'
    keywords = [field_to_append]
    max_len = len(original_field) + len('… ') + len(field_to_append)
    expected_field = f'{original_field}… {field_to_append}'

    actual_output = optimization_util.append_keywords_to_field(
        original_field, keywords, 0, max_len)

    self.assertEqual(expected_field, actual_output)

  def test_append_keywords_to_field_truncates_description_if_field_cannot_fit_in_whitespace(
      self):
    original_title = 'Original title'
    appended_desc = 'Description that can be truncated'
    original_field = f'{original_title}{appended_desc}'
    field_to_append = 'Field to append'
    max_len_modifier = 5
    max_len = len(original_title) + (len(appended_desc) - max_len_modifier)
    expected_field = 'Original titleDescription… Field to append'

    actual_output = optimization_util.append_keywords_to_field(
        original_field, [field_to_append], len(original_title), max_len)

    self.assertEqual(expected_field, actual_output)

  def test_append_keywords_to_field_does_not_split_numbers_when_description_truncated_to_fit_attributes(
      self):
    original_title = 'Original title'
    appended_desc = 'Description 1.2g that can be truncated'
    original_field = f'{original_title}{appended_desc}'
    field_to_append = 'Field to append'
    max_len_modifier = 7
    max_len = len(original_title) + (len(appended_desc) - max_len_modifier)
    expected_field = 'Original titleDescription… Field to append'

    actual_output = optimization_util.append_keywords_to_field(
        original_field, [field_to_append], len(original_title), max_len)

    self.assertEqual(expected_field, actual_output)

  def test_is_particular_google_product_category_returns_true_when_given_category_has_category_keyword(
      self):
    category = 'Apparel & Accessories > Shoes'
    category_keywords = ['Apparel & Accessories']

    result = optimization_util.is_particular_google_product_category(
        category, category_keywords, [])

    self.assertTrue(result)

  def test_is_particular_google_product_category_returns_false_when_given_category_does_not_have_category_keyword(
      self):
    category = 'Apparel & Accessories > Shoes'
    category_keywords = ['Health & Beauty']

    result = optimization_util.is_particular_google_product_category(
        category, category_keywords, [])

    self.assertFalse(result)

  def test_is_particular_google_product_category_returns_true_when_given_category_is_equal_to_one_of_category_ids(
      self):
    category = '1234'
    category_ids = ['1234', '5678']

    result = optimization_util.is_particular_google_product_category(
        category, [], category_ids)

    self.assertTrue(result)

  def test_is_particular_google_product_category_returns_false_when_given_category_is_not_equal_to_any_of_category_ids(
      self):
    category = '1234'
    category_ids = ['5678']

    result = optimization_util.is_particular_google_product_category(
        category, [], category_ids)

    self.assertFalse(result)

  def test_optimization_exclusion_specified_returns_true_if_attribute_was_specified_and_optimizer_matches(
      self):
    request_body = requests_bodies.build_request_body()
    exclude_optimizers = ['title-length-optimizer']
    request_body['entries'][0]['excludeOptimizers'] = exclude_optimizers

    result = optimization_util.optimization_exclusion_specified(
        request_body['entries'][0], 'title-length-optimizer')

    self.assertTrue(result)

  def test_optimization_exclusion_specified_returns_false_if_attribute_was_specified_but_optimizer_is_different(
      self):
    request_body = requests_bodies.build_request_body()
    exclude_optimizers = ['title-length-optimizer']
    request_body['entries'][0]['excludeOptimizers'] = exclude_optimizers

    result = optimization_util.optimization_exclusion_specified(
        request_body['entries'][0], 'promo-text-optimizer')

    self.assertFalse(result)

  def test_optimization_exclusion_specified_returns_false_if_attribute_was_not_specified(
      self):
    request_body = requests_bodies.build_request_body()
    result = optimization_util.optimization_exclusion_specified(
        request_body['entries'][0], 'title-length-optimizer')

    self.assertFalse(result)
