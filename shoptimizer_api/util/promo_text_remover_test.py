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

# python3
"""Unit tests for promo_text_remover.py."""
from typing import Any, Dict

from absl.testing import parameterized

from util import app_util
from util import promo_text_remover


def _build_dummy_product(title: str = '') -> Dict[str, Any]:
  """Builds a dummy product data.

  Args:
    title: A dummy title.

  Returns:
    A dummy product data.
  """
  return {
      'title': title,
  }


class PromoTextRemoverTest(parameterized.TestCase):

  def setUp(self):
    super(PromoTextRemoverTest, self).setUp()
    app_util.setup_test_app()
    self.text_remover = promo_text_remover.PromoTextRemover(language='test')

  def test_text_remover_does_not_change_empty_string(self):
    product = _build_dummy_product(title='')

    self.text_remover.remove_text_from_field(product, 'title')

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
      'original_title': '【限定クーポン配布中】 はんこ 【 送料無料 】ポイント消化 (TEST)',
      'expected_title': 'はんこ (TEST)'
  }])
  def test_text_remover_removes_text_by_regex(self, original_title,
                                              expected_title):
    product = _build_dummy_product(title=original_title)

    self.text_remover.remove_text_from_field(product, 'title')

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

    self.text_remover.remove_text_from_field(product, 'title')

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

    self.text_remover.remove_text_from_field(product, 'title')

    self.assertEqual(expected_title, product.get('title'))

  def test_text_remover_cleans_up_field_value(self):
    product = _build_dummy_product(title=' dummy title ')

    self.text_remover.remove_text_from_field(product, 'title')

    self.assertEqual('dummy title', product.get('title'))
