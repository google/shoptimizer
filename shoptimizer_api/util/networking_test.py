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

"""Tests for networking."""

from unittest import mock
import urllib.error
import urllib.request

from absl.testing import parameterized
from util import networking


class NetworkingTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.test_url = 'https://www.example.com/images/image.jpg'
    self.test_response = b'01'

    mock_urlopen = mock.MagicMock()
    mock_urlopen.read.return_value = self.test_response

    self.mock_urlopen = self.enter_context(
        mock.patch.object(urllib.request, 'urlopen',
                          return_value=mock_urlopen,
                          autospec=True))

  def test_load_bytes_at_url_requests_url(self):
    networking.load_bytes_at_url(self.test_url)
    self.mock_urlopen.assert_called_once_with(self.test_url)

  def test_load_bytes_at_url_returns_content_of_read(self):
    response = networking.load_bytes_at_url(self.test_url)
    self.assertEqual(response, self.test_response)

  def test_load_bytes_at_url_passes_through_urlerrors(self):
    with mock.patch.object(urllib.request, 'urlopen') as mock_request:
      mock_request.side_effect = urllib.error.HTTPError(
          self.test_url, 500, 'Internal Error', {}, None)

      with self.assertRaises(urllib.error.URLError):
        networking.load_bytes_at_url(self.test_url)
