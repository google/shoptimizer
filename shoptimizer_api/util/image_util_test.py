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

"""Tests for image_util."""
import os
import pathlib

from absl.testing import absltest
from util import image_util


_PATH_TO_TEST_IMAGES = os.path.join(
    pathlib.Path(__file__).parent.parent.resolve(), 'test_data')

_EXPECTED_ACCEPT_SCORE_MIN = 0
_EXPECTED_ACCEPT_SCORE_MAX = 0.5
_EXPECTED_DECLINE_SCORE_MIN = 0.5
_EXPECTED_DECLINE_SCORE_MAX = 1


def _saved_model_exists() -> bool:
  return os.path.isfile(
      os.path.join(image_util.MODEL_LOCATION, 'saved_model.pb'))


def _test_images_exist() -> bool:
  return os.path.isfile(
      os.path.join(_PATH_TO_TEST_IMAGES, 'accept.jpg')) and os.path.isfile(
          os.path.join(_PATH_TO_TEST_IMAGES, 'decline.jpg'))


class ImageUtilTest(absltest.TestCase):

  def test_score_image_returns_default_if_no_image_data_provided(self):
    self.assertEqual(image_util.DEFAULT_SCORE, image_util.score_image(None))

  def test_score_image_returns_default_if_image_data_empty(self):
    self.assertEqual(image_util.DEFAULT_SCORE, image_util.score_image(b''))

  @absltest.skipUnless(_saved_model_exists(),
                       f'Model file not found in {image_util.MODEL_LOCATION}.')
  def test_score_image_returns_default_if_invalid_image_provided(self):
    self.assertEqual(image_util.DEFAULT_SCORE,
                     image_util.score_image(b'1234567890'))

  @absltest.skipUnless(_saved_model_exists() and _test_images_exist(),
                       f'Required file(s) not found in {_PATH_TO_TEST_IMAGES}.')
  def test_score_accept_image_returns_score_in_expected_range(self):
    image_path = os.path.join(_PATH_TO_TEST_IMAGES, 'accept.jpg')
    with open(image_path, 'rb') as accept_image_file:
      score = image_util.score_image(accept_image_file.read())
      self.assertBetween(score,
                         _EXPECTED_ACCEPT_SCORE_MIN,
                         _EXPECTED_ACCEPT_SCORE_MAX)

  @absltest.skipUnless(_saved_model_exists() and _test_images_exist(),
                       f'Required file(s) not found in {_PATH_TO_TEST_IMAGES}.')
  def test_score_decline_image_returns_score_in_expected_range(self):
    image_path = os.path.join(_PATH_TO_TEST_IMAGES, 'decline.jpg')
    with open(image_path, 'rb') as decline_image_file:
      score = image_util.score_image(decline_image_file.read())
      self.assertBetween(score,
                         _EXPECTED_DECLINE_SCORE_MIN,
                         _EXPECTED_DECLINE_SCORE_MAX)

  def test_warns_and_returns_default_if_model_file_not_found(self):
    image_util.MODEL_LOCATION = '/'
    with self.assertLogs(level='WARNING') as logger:
      resulting_score = image_util.score_image(b'1234567890')
      self.assertIn(image_util.MODEL_LOCATION, logger.output[0])

    self.assertEqual(image_util.DEFAULT_SCORE, resulting_score)
