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

"""Unit tests for identity_optimizer.py."""
from absl.testing import parameterized

from optimizers_builtin import identity_optimizer
from test_data import requests_bodies


class IdentityOptimizerTest(parameterized.TestCase):

  def test_process_does_not_transform_data(self):
    original_data = requests_bodies.build_request_body()
    optimizer = identity_optimizer.IdentityOptimizer()

    optimized_data, _ = optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
