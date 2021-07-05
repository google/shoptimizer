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

"""Tests for image_link_optimizer.py."""

from typing import List

from absl.testing import parameterized

from optimizers_builtin import image_link_optimizer
from test_data import requests_bodies


def _build_list_of_image_links(num_links: int,
                               file_type: str = 'jpg') -> List[str]:
  return [f'https://examples.com/image{n}.{file_type}'
          for n in list(range(num_links))]


class ImageLinkOptimizerTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(ImageLinkOptimizerTest, self).setUp()
    self.optimizer = image_link_optimizer.ImageLinkOptimizer()
    self.valid_additional_image_links = _build_list_of_image_links(3)

  def test_optimizer_does_nothing_when_alternate_image_links_missing(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_removed=['additionalImageLink'])

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertNotIn('additionalImageLink', product)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_optimizer_does_nothing_when_alternate_image_links_valid(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={
            'additionalImageLink': self.valid_additional_image_links})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(self.valid_additional_image_links,
                     product['additionalImageLink'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_optimizer_does_not_remove_image_links_when_not_above_maximum(self):
    image_links = _build_list_of_image_links(10)

    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'additionalImageLink': image_links})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(image_links, product['additionalImageLink'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_optimizer_truncates_additional_images_above_maximum(self):
    image_links = _build_list_of_image_links(11)

    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'additionalImageLink': image_links})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(image_links[:10],
                     product['additionalImageLink'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)
