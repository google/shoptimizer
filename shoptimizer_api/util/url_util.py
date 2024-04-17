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

"""Common methods for validating URLs."""


import os
from typing import AnyStr, Optional
import urllib.parse

import constants


def is_valid_link_url(url: AnyStr, max_length: Optional[int] = None) -> bool:
  """Returns True if passed a valid link URL and False otherwise.

  Intended to assist with compliance with link and image_link URLs as
  specified here: https://support.google.com/merchants/answer/7052112.

  Valid link URLs:
    * Are no more than max_length characters in length.
    * Contain only ASCII characters.
    * Use either http or https schemes.
    * Use encoded URLs that comply with RFC 2396 or RFC 1738.

  Args:
    url: URL to validate.
    max_length: If present, check that the string length is no longer than this.

  Returns:
    True if the URL meets the criteria specified.
  """
  if max_length and len(url) > max_length:
    return False

  parsed_url = urllib.parse.urlsplit(url)

  if not url.isascii() or parsed_url.path != urllib.parse.quote(
      parsed_url.path, encoding='ASCII', errors='ignore'):
    return False

  if parsed_url.scheme.upper() not in ('HTTP', 'HTTPS'):
    return False

  return True


def is_valid_image_url(url: AnyStr, max_length: Optional[int] = None) -> bool:
  """Returns True if passed a valid link image_link URL and False otherwise.

  Intended to assist with compliance with image_link URLs as
  specified here: https://support.google.com/merchants/answer/7052112.

  Valid image_link URLs:
    * Meet the criteria of valid link_urls as in is_valid_link_url().
    * File suffixes are not required, but if a file suffix exists on the path,
      it must be an allowlisted suffix.

  Args:
    url: URL to validate.
    max_length: If present, check that the string length is no longer than this.

  Returns:
    True if the URL meets the criteria specified.
  """
  if is_valid_link_url(url, max_length):
    parsed_url = urllib.parse.urlparse(url)
    url_path = parsed_url.path.upper()
    suffix = os.path.splitext(url_path)[1]
    return not(suffix) or suffix in constants.VALID_IMAGE_URL_FILE_SUFFIXES

  return False

