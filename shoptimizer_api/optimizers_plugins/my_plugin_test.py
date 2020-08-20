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
"""Unit tests for my_plugin.py."""
from absl.testing import parameterized

from optimizers_plugins import my_plugin
from test_data import requests_bodies


class MyPluginTest(parameterized.TestCase):

  def test_process_does_not_transform_data(self):
    original_data = requests_bodies.VALID_SINGLE_PRODUCT
    optimizer = my_plugin.MyPlugin()

    optimized_data, _ = optimizer.process(original_data)

    self.assertEqual(original_data, optimized_data)
