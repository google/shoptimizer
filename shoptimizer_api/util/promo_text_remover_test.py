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

"""Unit tests for promo_text_remover.py."""
from typing import Any
from unittest import mock

from absl.testing import parameterized
import constants
from util import app_util
from util import promo_text_remover


def _build_dummy_product(title: str = '') -> dict[str, Any]:
  """Builds a dummy product data.

  Args:
    title: A dummy title.

  Returns:
    A dummy product data.
  """
  return {
      'title': title,
  }


@mock.patch(
    'util.promo_text_remover._PROMO_TEXT_REMOVAL_OPTIMIZER_CONFIG_FILE_NAME',
    'promo_text_removal_optimizer_config_{}_test')
class PromoTextRemoverTest(parameterized.TestCase):

  def setUp(self):
    super(PromoTextRemoverTest, self).setUp()
    app_util.setup_test_app()

  def test_text_remover_does_not_change_empty_string(self):
    product = _build_dummy_product(title='')

    text_remover = promo_text_remover.PromoTextRemover(
        language=constants.LANGUAGE_CODE_JA)
    text_remover.remove_text_from_field(product, 'title')

    self.assertEqual('', product.get('title'))

  @parameterized.named_parameters([{
      'testcase_name': 'one_pattern',
      'original_title': '[**removing this part**] dummy title',
      'expected_title': 'dummy title'
  }, {
      'testcase_name': 'two_patterns',
      'original_title': '[**removing this part**] dummy title removing pattern',
      'expected_title': 'dummy title'
  }, {
      'testcase_name': 'ja_patterns_multiple_brackets',
      'original_title': '【中古】【10倍ポイント】Tシャツ',
      'expected_title': '【中古】Tシャツ'
  }, {
      'testcase_name': 'ja_patterns_percent_off',
      'original_title': '【中古】【test 100%OFF! test】Tシャツ',
      'expected_title': '【中古】Tシャツ'
  }, {
      'testcase_name': 'ja_patterns_date',
      'original_title': '【12/25 まで！】【test】Tシャツ',
      'expected_title': '【test】Tシャツ'
  }, {
      'testcase_name': 'ja_multiple_bracket_types_mixed_with_exact_terms',
      'original_title':
          '【限定クーポン配布中】 はんこ 【 送料無料 '
          '】ポイント消化 (TEST)',
      'expected_title': 'はんこ (TEST)'
  }])
  def test_text_remover_removes_text_by_regex(self, original_title,
                                              expected_title):
    product = _build_dummy_product(title=original_title)

    text_remover = promo_text_remover.PromoTextRemover(
        language=constants.LANGUAGE_CODE_JA)
    text_remover.remove_text_from_field(product, 'title')

    self.assertEqual(expected_title, product.get('title'))

  @parameterized.named_parameters([{
      'testcase_name': 'one_text',
      'original_title': 'dummy title *removing this part',
      'expected_title': 'dummy title'
  }, {
      'testcase_name': 'two_texts',
      'original_title': 'dummy unnecessary text title *removing this part',
      'expected_title': 'dummy title'
  }])
  def test_text_remover_removes_text_by_exact_match(self, original_title,
                                                    expected_title):
    product = _build_dummy_product(title=original_title)

    text_remover = promo_text_remover.PromoTextRemover(
        language=constants.LANGUAGE_CODE_JA)
    text_remover.remove_text_from_field(product, 'title')

    self.assertEqual(expected_title, product.get('title'))

  @parameterized.named_parameters([{
      'testcase_name':
          'regex_first',
      'original_title':
          '[**removing this part**] dummy title*removing this part',
      'expected_title':
          'dummy title'
  }])
  def test_text_remover_removes_text_by_both_regex_and_exact_match(
      self, original_title, expected_title):
    product = _build_dummy_product(title=original_title)

    text_remover = promo_text_remover.PromoTextRemover(
        language=constants.LANGUAGE_CODE_JA)
    text_remover.remove_text_from_field(product, 'title')

    self.assertEqual(expected_title, product.get('title'))

  def test_text_remover_cleans_up_field_value(self):
    product = _build_dummy_product(title=' dummy title ')

    text_remover = promo_text_remover.PromoTextRemover(
        language=constants.LANGUAGE_CODE_JA)
    text_remover.remove_text_from_field(product, 'title')

    self.assertEqual('dummy title', product.get('title'))

  @parameterized.named_parameters([
      {
          'testcase_name':
              'one_promo_text_at_end_list_exact_match_should_be_removed',
          'list_with_promo': [
              'カイナ', '高い', '悪い', 'ポイント消化'
          ],
          'expected_result': {'カイナ', '高い', '悪い'}
      },
      {
          'testcase_name': 'promo_text_regex_pattern_pointo_is_removed',
          'list_with_promo': [
              'カイナ',
              '高い',
              '悪い',
              '【ポイント】'  # will be detected by our regex and removed
          ],
          'expected_result': {'カイナ', '高い', '悪い'}
      }
  ])
  def test_remove_keywords_with_promo(self, list_with_promo, expected_result):
    text_remover = promo_text_remover.PromoTextRemover(
        language=constants.LANGUAGE_CODE_JA)
    result = text_remover.remove_keywords_with_promo(list_with_promo)
    self.assertEqual(result, expected_result)
