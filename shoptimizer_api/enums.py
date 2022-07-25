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

"""Enums for use within the Shoptimizer API."""

import enum


class TrackingTag(enum.Enum):
  """Enums for optimization tracking.

  SANITIZED:
    Invalid data was removed or corrected. If this had not been done
    the product would have been disapproved.
  OPTIMIZED:
    Data was modified in an attempt to improve performance, but the
    original data was not incorrect.
  WMM:
    The product was optimized by title_word_order_optimizer using a
    word-mix-model.
  """
  SANITIZED = 'sanitized'
  OPTIMIZED = 'optimized'
  WMM = 'wmm'
