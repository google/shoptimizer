# coding=utf-8
# Copyright 2020 Google LLC.
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
"""Unit tests for base_optimizer.py."""
from typing import Any, Dict

import unittest.mock as mock

from absl.testing import parameterized

from optimizers_abstract import base_optimizer
from test_data import requests_bodies


class DummyOptimizer(base_optimizer.BaseOptimizer):
  """A dummy optimizer for testing (marks all products optimized)."""
  _OPTIMIZER_PARAMETER = 'dummy-optimizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    for entry in product_batch['entries']:
      product = entry['product']
      base_optimizer.set_optimization_tracking(product,
                                               base_optimizer.OPTIMIZED)

    return len(product_batch)  # Number of items Optimized.


class DummySanitizer(base_optimizer.BaseOptimizer):
  """A dummy sanitizer for testing (marks all products sanitized)."""
  _OPTIMIZER_PARAMETER = 'dummy-sanitizer'

  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    for entry in product_batch['entries']:
      product = entry['product']
      base_optimizer.set_optimization_tracking(product,
                                               base_optimizer.SANITIZED)

    return len(product_batch)  # Number of items Sanitized.


class BaseOptimizerTest(parameterized.TestCase):

  def test_optimizer_parameter_not_implemented_throws_not_implemented_error(
      self):

    class OptimizerWithNoUrlParameter(base_optimizer.BaseOptimizer):

      def _optimize(self, product_batch: Dict[str, Any], language: str,
                    country: str, currency: str) -> int:
        pass

    with self.assertRaises(NotImplementedError):
      optimizer = OptimizerWithNoUrlParameter()
      print(optimizer.optimizer_parameter)

  def test_optimize_not_implemented_throws_type_error(self):

    class OptimizerWithNoOptimizeMethod(base_optimizer.BaseOptimizer):
      _OPTIMIZER_PARAMETER = 'no-optimize'

    with self.assertRaises(TypeError):
      optimizer = OptimizerWithNoOptimizeMethod()
      optimizer.process({})

  def test_unhandled_error_returns_original_data_and_reports_failure(self):

    original_data = {'data': 'Not affected by optimization'}

    class OptimizerThatRaisesError(base_optimizer.BaseOptimizer):
      _OPTIMIZER_PARAMETER = 'raise-error'

      def _optimize(self, product_batch: Dict[str, Any], language: str,
                    country: str, currency: str):
        raise SystemError('Dummy error')

    optimizer = OptimizerThatRaisesError()

    returned_data, optimization_result = optimizer.process(original_data)

    self.assertEqual(original_data, returned_data)
    self.assertEqual('failure', optimization_result.result)
    self.assertEqual('Dummy error', optimization_result.error_msg)

  def test_set_optimization_tracking_returns_when_tracking_field_not_set(self):
    data = requests_bodies.build_request_body()
    dummy_optimizer = DummyOptimizer()
    tracking_field = ''

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = dummy_optimizer.process(data)
      optimized_product = optimized_data['entries'][0]['product']

      # Check none of the customLabel fields were set.
      # (Nothing else we can assert on here since there are no errors/
      #  log messages. It is valid for the tracking field to be blank.)
      self.assertEqual('', optimized_product['customLabel0'])
      self.assertEqual('', optimized_product['customLabel1'])
      self.assertEqual('', optimized_product['customLabel2'])
      self.assertEqual('', optimized_product['customLabel3'])
      self.assertEqual('', optimized_product['customLabel4'])

  def test_set_optimization_tracking_does_not_set_tracking_when_tracking_field_not_custom_label(
      self):
    data = requests_bodies.build_request_body()
    dummy_optimizer = DummyOptimizer()
    tracking_field = 'gtin'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = dummy_optimizer.process(data)
      optimized_product = optimized_data['entries'][0]['product']

      self.assertNotEqual(base_optimizer.OPTIMIZED, optimized_product['gtin'])

  def test_set_optimization_tracking_sets_tracking_field_to_optimized(self):
    data = requests_bodies.build_request_body()
    dummy_optimizer = DummyOptimizer()
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = dummy_optimizer.process(data)
      optimized_product = optimized_data['entries'][0]['product']

      self.assertNotEqual(base_optimizer.OPTIMIZED,
                          optimized_product[tracking_field])

  def test_set_optimization_tracking_sets_tracking_field_to_sanitized(self):
    data = requests_bodies.build_request_body()
    dummy_sanitizer = DummySanitizer()
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = dummy_sanitizer.process(data)
      optimized_product = optimized_data['entries'][0]['product']

      self.assertNotEqual(base_optimizer.SANITIZED,
                          optimized_product[tracking_field])

  def test_set_optimization_tracking_sets_tracking_field_sanitized_optimized_when_product_optimized_then_sanitized(
      self):
    data = requests_bodies.build_request_body()
    dummy_optimizer = DummyOptimizer()
    dummy_sanitizer = DummySanitizer()
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      sanitized_data, _ = dummy_sanitizer.process(data)
      optimized_data, _ = dummy_optimizer.process(sanitized_data)
      optimized_product = optimized_data['entries'][0]['product']

      self.assertNotEqual(base_optimizer.SANITIZED_AND_OPTIMIZED,
                          optimized_product[tracking_field])

  def test_set_optimization_tracking_sets_tracking_field_sanitized_optimized_when_product_sanitized_then_optimized(
      self):
    data = requests_bodies.build_request_body()
    dummy_optimizer = DummyOptimizer()
    dummy_sanitizer = DummySanitizer()
    tracking_field = 'customLabel4'

    with mock.patch.dict('os.environ',
                         {'PRODUCT_TRACKING_FIELD': tracking_field}):
      optimized_data, _ = dummy_optimizer.process(data)
      sanitized_data, _ = dummy_sanitizer.process(optimized_data)
      sanitized_product = sanitized_data['entries'][0]['product']

      self.assertNotEqual(base_optimizer.SANITIZED_AND_OPTIMIZED,
                          sanitized_product[tracking_field])
