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

"""A module for Shoptimizer API handling image_link and additional_image_link.

References: https://support.google.com/merchants/answer/6324350
  and https://support.google.com/merchants/answer/6324370

Products that have invalid image_link attributes will be disapproved. Those with
  invalid additional_image_link attributes will be flagged but not disapproved.
"""

import logging
from typing import Any, Dict

from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import optimization_util


_MAX_ALT_IMAGES: int = 10


class ImageLinkOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer for image_link and additional_image_link attributes.

  Validates the content of these fields and if both:
   * image_link is likely to be disapproved
   * at least one image in additional_image_link is not likely to be disapproved

  then swaps the image_link image with the best additional_image_link image.
  """

  _OPTIMIZER_PARAMETER = 'image-link-optimizer'

  def _optimize(
      self,
      product_batch: Dict[str, Any],
      language: str,
      country: str,
      currency: str
      ) -> optimization_result_counts.OptimizationResultCounts:
    """Runs the optimization.

    Sanitizes invalid additional_image_link attributes if they:
      * Contain more than _MAX_ALT_IMAGES images

    Args:
      product_batch: A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected and excluded by this optimization.
    """
    num_of_products_optimized = 0
    num_of_products_excluded = 0

    for entry in product_batch['entries']:

      if (optimization_util.optimization_exclusion_specified(
          entry, self._OPTIMIZER_PARAMETER)):
        num_of_products_excluded += 1
        continue

      product = entry['product']
      if 'additionalImageLink' in product:
        alt_image_links = product['additionalImageLink']

        if len(alt_image_links) > _MAX_ALT_IMAGES:
          product_id = product.get('offerId', '')
          num_images_removed = len(alt_image_links) - _MAX_ALT_IMAGES
          product['additionalImageLink'] = alt_image_links[:_MAX_ALT_IMAGES]

          logging.info('Modified item `%s`: Truncating additionalImageLink '
                       'to %s images (Removed %s images).',
                       product_id, _MAX_ALT_IMAGES, num_images_removed)
          num_of_products_optimized += 1
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.SANITIZED)

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)
