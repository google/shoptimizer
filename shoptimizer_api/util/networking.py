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

"""Common methods for interacting with the internet or other remote APIs.
"""

import urllib.error
import urllib.request


def load_bytes_at_url(url: str) -> bytes:
  """Returns bytes present in the content of the provided URL.

  Args:
    url: The file to download.

  Returns:
    Contents of the file at the URL.

  Raises:
    urllib.error.URLError: Upon encountering an error with the request.
  """
  http_response = urllib.request.urlopen(url)
  return http_response.read()


