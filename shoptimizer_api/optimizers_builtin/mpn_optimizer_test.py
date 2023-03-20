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

"""Unit tests for mpn_optimizer.py."""

from typing import Any, Dict, Optional
import unittest.mock as mock

from absl.testing import parameterized

import enums
from optimizers_builtin import mpn_optimizer
from test_data import requests_bodies


def _build_request_body(has_mpn_field: bool,
                        mpn_value: Optional[str] = None) -> Dict[str, Any]:
  """Builds a dummy request body.

  Request body includes 1 product with specific mpn value or without mpn.

  Args:
    has_mpn_field: Whether the request body should have mpn field or not.
    mpn_value: The mpn value of the product.

  Returns:
    A dummy request body including 1 product.
  """
  properties_to_be_removed = []
  if not has_mpn_field:
    properties_to_be_removed.append('mpn')
  body = requests_bodies.build_request_body({'mpn': mpn_value},
                                            properties_to_be_removed)
  return body


class MPNOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(MPNOptimizerTest, self).setUp()
    self.optimizer = mpn_optimizer.MPNOptimizer()

  @parameterized.parameters(mpn for mpn in mpn_optimizer.INVALID_MPN_VALUES)
  def test_process_removes_mpn_field_when_its_value_invalid(
      self, invalid_mpn):
    original_data = _build_request_body(True, invalid_mpn)

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertNotIn('mpn', optimized_data['entries'][0]['product'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_removes_mpn_field_when_its_value_invalid_after_normalized(
      self):
    invalid_mpn = 'N/A'
    original_data = _build_request_body(True, invalid_mpn)

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertNotIn('mpn', optimized_data['entries'][0]['product'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_process_does_not_transform_data_when_mpn_valid(self):
    original_data = _build_request_body(True, 'valid-mpn')

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_does_not_transform_data_when_mpn_field_not_exist(self):
    original_data = _build_request_body(False)

    optimized_data, optimization_result = self.optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_process_sets_product_tracking_field_to_sanitized_when_invalid_mpn_value_removed(
      self):
    invalid_mpn_value = 'default'
    original_data = _build_request_body(True, invalid_mpn_value)
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = self.optimizer.process(original_data)
      optimized_product = optimized_data['entries'][0]['product']

      self.assertEqual(enums.TrackingTag.SANITIZED.value,
                       optimized_product[tracking_field])
