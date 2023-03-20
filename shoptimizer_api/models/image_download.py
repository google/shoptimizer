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

"""Stores image download data and metadata."""
import dataclasses
from typing import Optional


@dataclasses.dataclass(order=True, frozen=False)
class ImageDownload(object):
  """Stores the content of an image download.

  Sorting ImageDownload in ascending order should return them in priority order.
  """
  image_invalid: bool
  score: float
  original_index: int
  url: str
  content: Optional[bytes] = None
