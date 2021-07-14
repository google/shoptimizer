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

"""Tests for url_util."""
from absl.testing import parameterized
import constants
from util import url_util

_VALID_ASCII_URLS = [
    'http://foo.com/dir',
    'http://foo.com/dir/',
    'http://foo.com/dir/file.extension',
    'https://www.example.com/foo/?bar=baz&quux',
    'http://userid:password@example.com:8080'
]

_INVALID_ASCII_URLS = [
    ('not a url', 'test_text'),
    ('non-ascii domain with http', 'http://➡.com'),
    ('non-ascii domain with https', 'https://➡.com'),
    ('ftp', 'ftp://google.com')]

_INVALID_IMAGE_URL_FILE_SUFFIXES = ('.AI', '.ICO', '.MOV', '.SVG', '.TTF')


class UrlUtilTest(parameterized.TestCase):

  @parameterized.named_parameters((u, u) for u in _VALID_ASCII_URLS)
  def test_is_valid_link_url_allows_valid_urls(self, url):
    self.assertTrue(url_util.is_valid_link_url(url))

  @parameterized.named_parameters(_INVALID_ASCII_URLS)
  def test_is_valid_link_url_disallows_invalid_urls(self, url):
    self.assertFalse(url_util.is_valid_link_url(url))

  def test_is_valid_link_url_disallows_urls_longer_than_maxlength(self):
    self.assertFalse(url_util.is_valid_link_url('https://g.co', 10))

  @parameterized.named_parameters(
      (ext.upper(), ext.upper())
      for ext in constants.VALID_IMAGE_URL_FILE_SUFFIXES)
  def test_is_valid_image_url_allows_valid_uppercase_file_suffixes(self, ext):
    self.assertTrue(url_util.is_valid_image_url(f'https://g.co/image{ext}'))

  @parameterized.named_parameters(
      (ext.lower(), ext.lower())
      for ext in constants.VALID_IMAGE_URL_FILE_SUFFIXES
  )
  def test_is_valid_image_url_allows_valid_lowercase_file_suffixes(self, ext):
    self.assertTrue(url_util.is_valid_image_url(f'https://g.co/image{ext}'))

  def test_is_valid_image_url_allows_missing_file_suffix(self):
    self.assertTrue(url_util.is_valid_image_url('https://g.co/image'))

  @parameterized.named_parameters(
      (ext, ext) for ext in _INVALID_IMAGE_URL_FILE_SUFFIXES)
  def test_is_valid_image_url_disallows_invalid_file_suffixes(self, ext):
    self.assertFalse(url_util.is_valid_image_url(f'https://g.co/image{ext}'))

  @parameterized.named_parameters(_INVALID_ASCII_URLS)
  def test_is_valid_image_url_disallows_invalid_urls(self, url):
    self.assertFalse(url_util.is_valid_image_url(url))

  def test_is_valid_image_url_disallows_urls_longer_than_maxlength(self):
    self.assertFalse(url_util.is_valid_image_url('https://g.co/image.jpg', 10))

