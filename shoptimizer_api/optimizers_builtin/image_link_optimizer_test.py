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

"""Tests for image_link_optimizer.py."""
import json
import time
from typing import Any, Dict, Iterable, List
from unittest import mock
import urllib.error

from absl.testing import absltest
import constants
import flask
from optimizers_builtin import image_link_optimizer
from test_data import requests_bodies
from util import app_util
from util import image_util
from util import networking


def _build_list_of_image_links(num_links: int,
                               file_type: str = 'jpg') -> List[str]:
  return [f'https://examples.com/image{n}.{file_type}'
          for n in list(range(num_links))]


def _request_body_from_image_links(links: Iterable[str]) -> Dict[str, Any]:
  return requests_bodies.build_request_body(properties_to_be_updated={
      'imageLink': links[0],
      'additionalImageLink': links[1:]
  })


def _setup_flask_with_configs_only():
  app = flask.Flask(__name__)
  app.config['CONFIGS'] = app_util._load_all_configs()
  app.app_context().push()


@mock.patch.object(image_link_optimizer, '_CONFIG_FILE_NAME',
                   new='image_link_optimizer_config_test')
class ImageLinkOptimizerTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    _setup_flask_with_configs_only()

    # By default, mock load_bytes_at_url to return empty bytes
    self.mock_urlopen = self.enter_context(
        mock.patch.object(networking, 'load_bytes_at_url', return_value=b'',
                          autospec=True))

    # By default, mock the ML model to avoid scoring each image
    self.mock_model = self.enter_context(
        mock.patch.object(image_util, 'score_image', return_value=float('inf'),
                          autospec=True))

    self.optimizer = image_link_optimizer.ImageLinkOptimizer(
        image_link_optimizer.CONFIGURATION_DEFAULTS)

  def test_config_uses_defaults_if_no_config_file_or_assignment(self):
    with mock.patch.object(image_link_optimizer, '_CONFIG_FILE_NAME', 'file'):
      optimizer = image_link_optimizer.ImageLinkOptimizer()
      self.assertEqual(
          image_link_optimizer
          .CONFIGURATION_DEFAULTS['require_image_can_be_downloaded'],
          optimizer.require_image_can_be_downloaded)
      self.assertEqual(
          image_link_optimizer
          .CONFIGURATION_DEFAULTS['require_image_score_quality_better_than'],
          optimizer.require_image_score_quality_better_than)

  def test_config_uses_config_file_if_no_assignment(self):
    with open(f'config/{image_link_optimizer._CONFIG_FILE_NAME}.json') as f:
      file_config = json.load(f)
      optimizer = image_link_optimizer.ImageLinkOptimizer()

      self.assertEqual(
          file_config['require_image_can_be_downloaded'],
          optimizer.require_image_can_be_downloaded)
      self.assertEqual(
          file_config['require_image_score_quality_better_than'],
          optimizer.require_image_score_quality_better_than)

  def test_config_uses_assignment_if_available(self):
    assignments = {
        'require_image_can_be_downloaded': True,
        'require_image_score_quality_better_than': float('inf')
    }
    optimizer = image_link_optimizer.ImageLinkOptimizer(assignments)

    self.assertEqual(
        assignments['require_image_can_be_downloaded'],
        optimizer.require_image_can_be_downloaded)
    self.assertEqual(
        assignments['require_image_score_quality_better_than'],
        optimizer.require_image_score_quality_better_than)

  def test_negative_require_image_score_quality_better_than_set_to_zero(self):
    optimizer = image_link_optimizer.ImageLinkOptimizer({
        'require_image_score_quality_better_than': -1
    })

    self.assertEqual(0, optimizer.require_image_score_quality_better_than)

  def test_raises_if_invalid_require_image_score_quality_better_than(self):
    with self.assertRaises(ValueError):
      image_link_optimizer.ImageLinkOptimizer({
          'require_image_score_quality_better_than': 'some string'
      })

  def test_optimizer_does_nothing_when_alternate_image_links_missing(self):
    original_data = requests_bodies.build_request_body(
        properties_to_be_removed=['additionalImageLink'])

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertNotIn('additionalImageLink', product)
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_optimizer_does_nothing_when_alternate_image_links_valid(self):
    image_links = _build_list_of_image_links(3)
    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'additionalImageLink': image_links})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(image_links, product['additionalImageLink'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_optimizer_does_not_remove_image_links_when_not_above_maximum(self):
    image_links = _build_list_of_image_links(constants.MAX_ALTERNATE_IMAGE_URLS)

    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'additionalImageLink': image_links})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(image_links, product['additionalImageLink'])
    self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_optimizer_truncates_additional_images_above_maximum(self):
    image_links = _build_list_of_image_links(
        constants.MAX_ALTERNATE_IMAGE_URLS + 1)

    original_data = requests_bodies.build_request_body(
        properties_to_be_updated={'additionalImageLink': image_links})

    optimized_data, optimization_result = self.optimizer.process(original_data)
    product = optimized_data['entries'][0]['product']

    self.assertEqual(image_links[:constants.MAX_ALTERNATE_IMAGE_URLS],
                     product['additionalImageLink'])
    self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_optimizer_requests_data_from_all_image_urls(self):
    image_links = _build_list_of_image_links(3)
    self.optimizer.process(_request_body_from_image_links(image_links))

    self.mock_urlopen.assert_has_calls(
        [mock.call(image_links[0]),
         mock.call(image_links[1]),
         mock.call(image_links[2])],
        any_order=True)

  def test_doesnt_download_urls_if_not_require_image_can_be_downloaded(self):
    image_links = _build_list_of_image_links(3)
    optimizer = image_link_optimizer.ImageLinkOptimizer({
        'require_image_can_be_downloaded': False
    })

    optimizer.process(_request_body_from_image_links(image_links))

    self.mock_urlopen.assert_not_called()

  def test_doesnt_attempt_scoring_if_not_require_image_can_be_downloaded(self):
    image_links = _build_list_of_image_links(3)
    optimizer = image_link_optimizer.ImageLinkOptimizer({
        'require_image_can_be_downloaded': False
    })

    optimizer.process(_request_body_from_image_links(image_links))

    self.mock_model.assert_not_called()

  def test_optimizer_does_not_request_from_nonhttp_urls(self):
    image_links = _build_list_of_image_links(2)
    image_links[0] = 'ftp://google.com/image.jpg'

    self.optimizer.process(_request_body_from_image_links(image_links))

    self.assertNotIn(
        mock.call(image_links[0]), self.mock_urlopen.call_args_list)

  def test_optimizer_does_not_request_from_long_urls(self):
    image_links = _build_list_of_image_links(2)
    many_zeros = '0' * constants.MAX_IMAGE_URL_LENGTH
    image_links[0] = f'https://google.com/image{many_zeros}.jpg'

    self.optimizer.process(_request_body_from_image_links(image_links))

    self.assertNotIn(
        mock.call(image_links[0]), self.mock_urlopen.call_args_list)

  def test_does_not_remove_additional_images_with_errors_below_max(self):
    image_links = _build_list_of_image_links(3)
    responses = [b''] * len(image_links)
    responses[1] = urllib.error.HTTPError(image_links[1], 500, 'Internal Error',
                                          {}, None)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimized_data, optimization_result = self.optimizer.process(
          _request_body_from_image_links(image_links))
      product = optimized_data['entries'][0]['product']

      self.assertEqual(image_links[0], product['imageLink'])
      self.assertEqual(image_links[1:], product['additionalImageLink'])
      self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_scores_all_valid_images(self):
    image_links = _build_list_of_image_links(3)
    responses = bytearray('ABCDEF', 'ASCII')

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      self.optimizer.process(_request_body_from_image_links(image_links))

      self.mock_model.assert_has_calls([
          mock.call(responses[0]),
          mock.call(responses[1]),
          mock.call(responses[2])
      ], any_order=True)

  def test_does_not_score_images_with_no_content(self):
    image_links = _build_list_of_image_links(3)
    responses = [b''] * len(image_links)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      self.optimizer.process(_request_body_from_image_links(image_links))

      self.mock_model.assert_not_called()

  def test_does_not_score_images_if_minimum_score_is_infinite(self):
    image_links = _build_list_of_image_links(3)

    assignments = {
        'require_image_can_be_downloaded': True,
        'require_image_score_quality_better_than': float('inf')
    }
    optimizer = image_link_optimizer.ImageLinkOptimizer(assignments)
    responses = bytearray('ABCDEF', 'ASCII')

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimizer.process(_request_body_from_image_links(image_links))

      self.mock_model.assert_not_called()

  def test_does_not_score_images_with_url_errors(self):
    image_links = _build_list_of_image_links(3)
    responses = [urllib.error.HTTPError(link, 500, 'Internal Error', {}, None)
                 for link in image_links]

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      self.optimizer.process(_request_body_from_image_links(image_links))

      self.mock_model.assert_not_called()

  def test_preferentially_removes_images_with_invalid_urls(self):
    image_links = _build_list_of_image_links(
        constants.MAX_ALTERNATE_IMAGE_URLS + 2)
    image_links[1] = 'ftp://google.com/image.jpg'
    responses = [b''] * len(image_links)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimized_data, optimization_result = self.optimizer.process(
          _request_body_from_image_links(image_links))
      product = optimized_data['entries'][0]['product']

      # Expect to remove the 1st additional image link
      expected_links = image_links[2:]
      self.assertEqual(image_links[0], product['imageLink'])
      self.assertEqual(expected_links, product['additionalImageLink'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_preferentially_removes_images_above_size_limit(self):
    image_links = _build_list_of_image_links(
        constants.MAX_ALTERNATE_IMAGE_URLS + 2)
    responses = [b''] * len(image_links)
    responses[1] = b'0' * (constants.MAX_IMAGE_FILE_SIZE_BYTES + 1)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimized_data, optimization_result = self.optimizer.process(
          _request_body_from_image_links(image_links))
      product = optimized_data['entries'][0]['product']

      # Expect to remove the 1st additional image link
      expected_links = image_links[2:]
      self.assertEqual(image_links[0], product['imageLink'])
      self.assertEqual(expected_links, product['additionalImageLink'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_preferentially_removes_images_with_errors_above_max(self):
    image_links = _build_list_of_image_links(13)
    responses = [b''] * len(image_links)
    responses[4] = urllib.error.HTTPError(image_links[4], 500,
                                          'Internal Error', {}, None)
    responses[8] = urllib.error.HTTPError(image_links[8], 500,
                                          'Internal Error', {}, None)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimized_data, optimization_result = self.optimizer.process(
          _request_body_from_image_links(image_links))
      product = optimized_data['entries'][0]['product']

      # Expect to remove the 4th and 8th image due to errors
      expected_links = image_links[1:4] + image_links[5:8] + image_links[9:]
      self.assertEqual(image_links[0], product['imageLink'])
      self.assertEqual(expected_links, product['additionalImageLink'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_first_removes_errors_above_max_then_truncates_at_max(self):
    image_links = _build_list_of_image_links(13)
    responses = [b''] * len(image_links)
    responses[4] = urllib.error.HTTPError(image_links[1], 500,
                                          'Internal Error', {}, None)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimized_data, optimization_result = self.optimizer.process(
          _request_body_from_image_links(image_links))
      product = optimized_data['entries'][0]['product']

      # Expect to remove the 4th image due to error and the last from truncation
      expected_links = image_links[1:4] + image_links[5:-1]
      self.assertEqual(image_links[0], product['imageLink'])
      self.assertEqual(expected_links, product['additionalImageLink'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_swaps_on_primary_image_error_with_alternate_available(self):
    image_links = _build_list_of_image_links(3)
    responses = [b''] * len(image_links)
    responses[0] = urllib.error.HTTPError(image_links[0], 500,
                                          'Internal Error', {}, None)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimized_data, optimization_result = self.optimizer.process(
          _request_body_from_image_links(image_links))
      product = optimized_data['entries'][0]['product']

      self.assertEqual(image_links[1], product['imageLink'])
      expected_links = [image_links[0]] + image_links[2:]
      self.assertEqual(expected_links, product['additionalImageLink'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_swaps_on_primary_image_error_with_any_alternate_available(self):
    image_links = _build_list_of_image_links(3)
    responses = [b''] * len(image_links)
    responses[0] = urllib.error.HTTPError(image_links[0], 500,
                                          'Internal Error', {}, None)
    responses[1] = urllib.error.HTTPError(image_links[1], 500,
                                          'Internal Error', {}, None)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimized_data, optimization_result = self.optimizer.process(
          _request_body_from_image_links(image_links))
      product = optimized_data['entries'][0]['product']

      self.assertEqual(image_links[2], product['imageLink'])
      # Ensure imageLink swapped with 2nd alternate, since the 1st is an error
      expected_links = [image_links[1], image_links[0]]
      self.assertEqual(expected_links, product['additionalImageLink'])
      self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_preferentially_chooses_lowest_scoring_image(self):
    image_links = _build_list_of_image_links(5)
    image_responses = [b'101010'] * len(image_links)
    image_responses[0] = urllib.error.HTTPError(image_links[0], 500,
                                                'Internal Error', {}, None)
    score_responses = [0.75, 0.5, 0.25, 1.0]

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_network:
      mock_network.side_effect = image_responses

      with mock.patch.object(image_util, 'score_image') as mock_model:
        mock_model.side_effect = score_responses

        optimized_data, optimization_result = self.optimizer.process(
            _request_body_from_image_links(image_links))
        product = optimized_data['entries'][0]['product']

        # Ensure imageLink swapped with 3rd alternate; that has the lowest score
        self.assertEqual(image_links[3], product['imageLink'])
        expected_links = [image_links[1], image_links[2],
                          image_links[0], image_links[4]]
        self.assertEqual(expected_links, product['additionalImageLink'])
        self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_images_scoring_below_threshold_are_considered_invalid(self):
    image_links = _build_list_of_image_links(3)
    image_responses = [b'101010'] * len(image_links)
    score_responses = [0.75, 0.25, 1.0]
    assignments = {
        'require_image_can_be_downloaded': True,
        'require_image_score_quality_better_than': 0.5
    }
    optimizer = image_link_optimizer.ImageLinkOptimizer(assignments)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_network:
      mock_network.side_effect = image_responses

      with mock.patch.object(image_util, 'score_image') as mock_model:
        mock_model.side_effect = score_responses

        optimized_data, optimization_result = optimizer.process(
            _request_body_from_image_links(image_links))
        product = optimized_data['entries'][0]['product']

        # Ensure imageLink swapped with 1st alternate; that has the lowest score
        self.assertEqual(image_links[1], product['imageLink'])
        expected_links = [image_links[0], image_links[2]]
        self.assertEqual(expected_links, product['additionalImageLink'])
        self.assertEqual(1, optimization_result.num_of_products_optimized)

  def test_do_not_swap_images_if_better_alternates_score_below_threshold(self):
    image_links = _build_list_of_image_links(3)
    image_responses = [b'101010'] * len(image_links)
    score_responses = [0.75, 0.6, 0.7]
    assignments = {
        'require_image_can_be_downloaded': True,
        'require_image_score_quality_better_than': 0.5
    }
    optimizer = image_link_optimizer.ImageLinkOptimizer(assignments)

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_network:
      mock_network.side_effect = image_responses

      with mock.patch.object(image_util, 'score_image') as mock_model:
        mock_model.side_effect = score_responses

        optimized_data, optimization_result = optimizer.process(
            _request_body_from_image_links(image_links))
        product = optimized_data['entries'][0]['product']

      self.assertEqual(image_links[0], product['imageLink'])
      self.assertEqual(image_links[1:], product['additionalImageLink'])
      self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_does_not_swap_on_primary_image_error_if_no_alternate_available(self):
    image_links = _build_list_of_image_links(3)
    responses = [urllib.error.HTTPError(link, 500, 'Internal Error', {}, None)
                 for link in image_links]

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = responses

      optimized_data, optimization_result = self.optimizer.process(
          _request_body_from_image_links(image_links))
      product = optimized_data['entries'][0]['product']

      self.assertEqual(image_links[0], product['imageLink'])
      self.assertEqual(image_links[1:], product['additionalImageLink'])
      self.assertEqual(0, optimization_result.num_of_products_optimized)

  def test_downloads_images_in_parallel(self):
    sleep_amount_secs = 0.25
    image_links = _build_list_of_image_links(3)

    def _wait_before_responding(*_args):
      time.sleep(sleep_amount_secs)
      return b''

    with mock.patch.object(networking, 'load_bytes_at_url') as mock_request:
      mock_request.side_effect = _wait_before_responding

      start_time = time.time()
      self.optimizer.process(_request_body_from_image_links(image_links))
      end_time = time.time()

      # Elapsed time < sum of the sleep times iff requests are in parallel
      self.assertLess(end_time - start_time,
                      len(image_links) * sleep_amount_secs)
