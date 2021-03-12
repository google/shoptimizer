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

"""Unit tests for optimizer_cache.py."""
import unittest.mock as mock

from absl.testing import parameterized

from optimizers_abstract import base_optimizer
from optimizers_utils import optimizer_cache


class OptimizerCacheTest(parameterized.TestCase):
  """Unit tests for optimizer_cache.py.

  It is difficult to test this class since it involves dynamically loading
  classes from a code base that is changing. Therefore, tests focus on three
  things:

  0. At least 1 (> 0) optimizer is loaded.
  1. Only instances of base_optimizer are loaded.
  2. Calling the optimizer_classes property more than once does not load
     optimizer classes again since they are already loaded.
  """

  def test_optimizers_are_loaded(self):
    builtin_optimizers_package_name = '../optimizers_builtin'
    cache = optimizer_cache.OptimizerCache(builtin_optimizers_package_name)

    optimizer_classes = cache.optimizer_classes

    self.assertEmpty(optimizer_classes)

  def test_only_implementations_of_base_optimizer_are_loaded(self):
    builtin_optimizers_package_name = '../optimizers_builtin'
    cache = optimizer_cache.OptimizerCache(builtin_optimizers_package_name)

    optimizer_classes = cache.optimizer_classes

    for optimizer_class in optimizer_classes:
      self.assertTrue(issubclass(optimizer_class, base_optimizer.BaseOptimizer))

  def test_optimizers_only_loaded_once(self):
    builtin_optimizers_package_name = '../optimizers_builtin'

    with mock.patch(
        'optimizers_utils.optimizer_cache.OptimizerCache._get_optimizer_classes_in_package'
    ) as mock_get_optimizer_classes_in_package:
      cache = optimizer_cache.OptimizerCache(builtin_optimizers_package_name)
      # Calls the optimizer_classes property several times to make sure loading
      # only gets called once.
      _ = cache.optimizer_classes
      _ = cache.optimizer_classes
      _ = cache.optimizer_classes

      self.assertEqual(1, mock_get_optimizer_classes_in_package.call_count)
