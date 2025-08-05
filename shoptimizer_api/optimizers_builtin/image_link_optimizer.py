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

"""A module for Shoptimizer API handling image_link and additional_image_link.

References: https://support.google.com/merchants/answer/6324350
  and https://support.google.com/merchants/answer/6324370

Products that have invalid image_link attributes will be disapproved. Those with
  invalid additional_image_link attributes will be flagged but not disapproved.
"""

import concurrent.futures
import logging
import math
import os
import sys
from typing import Any, Iterable, List, Mapping, Tuple
import urllib.error

import constants
import flask
from models import image_download
from models import optimization_result_counts
from optimizers_abstract import base_optimizer
from util import image_util
from util import networking
from util import optimization_util
from util import url_util

_CONFIG_FILE_NAME: str = 'image_link_optimizer_config'
_THREAD_NAME_PREFIX: str = 'shoptimizer-image-optimizer'

CONFIGURATION_DEFAULTS = {
    'require_image_can_be_downloaded': True,
    'require_image_score_quality_better_than': 0.9
}


class ImageLinkOptimizer(base_optimizer.BaseOptimizer):
  """An optimizer for image_link and additional_image_link attributes.

  Validates the content of these fields and if both:
   * image_link is likely to be disapproved
   * at least one image in additional_image_link is not likely to be disapproved

  then swaps the image_link image with the best additional_image_link image.

  Attributes below are configuration options that affect images referred to in
  the image_link and additional_image_link fields within each product.

  Attributes:
    require_image_can_be_downloaded: (bool) If True, image URLs must be
      reachable by this optimizer; image file size is also validated.
      Required for image scoring.
      If False, do not try to download this image.
    require_image_score_quality_better_than: (float) Consider images likely to
      be diapproved if their quality score is worse than this value.
      Requires images to be downloaded.
      Normal scores range from 0.0 (best) to 1.0 (worst). Set to 'inf' to
      disable scoring. Read the documentation for more complete guidance on this
      attribute.
  """

  _OPTIMIZER_PARAMETER = 'image-link-optimizer'

  def __init__(self, configuration_options: Mapping[str, Any] = None) -> None:
    """Initializes ImageLinkOptimizer.

    Populates configuration information.

    Sets the number max number of available threads according to the default
    for ThreadPoolExecutor, since this is expected to be IO bound:
    https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor

    Args:
      configuration_options: Optionally specified overrides for the attributes
      of this class; will override the default configuration file options.
    """
    super(ImageLinkOptimizer, self).__init__()
    self._max_available_threads = min(32, os.cpu_count() + 4)

    self._load_configuration_with_defaults(configuration_options)

  def _load_configuration_with_defaults(self,
                                        override_config: Mapping[str,
                                                                 Any] = None
                                       ) -> Mapping[str, Any]:
    """Loads the configuration for this Optimizer considering defaults.

    Loads the configuration from override_config if provided, then
    configuration file (if available), and sets conservative defaults if no
    other configuration is available.

    Args:
      override_config: Optionally specified configuration options that will
      override the config-file and default configuration options if present.
    """
    file_config = flask.current_app.config.get('CONFIGS', {}).get(
        _CONFIG_FILE_NAME, {})

    loaded_config = dict()
    for config, default in CONFIGURATION_DEFAULTS.items():
      loaded_config[config] = file_config.get(config, default)
      if override_config and config in override_config:
        loaded_config[config] = override_config[config]

    self.require_image_can_be_downloaded = bool(
        loaded_config.get('require_image_can_be_downloaded'))
    self.require_image_score_quality_better_than = max(0, float(
        loaded_config.get('require_image_score_quality_better_than')))

  def _optimize(
      self,
      product_batch: Mapping[str, Any],
      language: str,
      country: str,
      currency: str
      ) -> optimization_result_counts.OptimizationResultCounts:
    """Runs the optimization.

    Optimizes image_link and additional_image_link URLs if:
      * The referenced URLs are not accessible via HTTP.

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
      product_id = product.get('offerId', '')
      product_optimized = False

      if 'additionalImageLink' in product and product['additionalImageLink']:
        original_image_link = product['imageLink']
        alt_image_links = product['additionalImageLink']

        # Combine original and alternate images for parallel processing,
        # then split up again afterwards.
        image_links = [original_image_link] + alt_image_links
        images = self._process_images_in_parallel(image_links)
        original_image = images.pop(0)
        images, num_images_removed = _truncate_excess_images(images)

        if num_images_removed:
          product['additionalImageLink'] = [image.url for image in images]
          logging.info('Modified item `%s`: Truncating additionalImageLink '
                       'to %s images (Removed %s images).',
                       product_id, constants.MAX_ALTERNATE_IMAGE_URLS,
                       num_images_removed)
          product_optimized = True
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.SANITIZED)

        if original_image.image_invalid and any(
            not(alt_image.image_invalid) for alt_image in images):
          product = _swap_original_image_with_best_alternative(
              product, original_image, images)
          product_optimized = True
          base_optimizer.set_optimization_tracking(product,
                                                   base_optimizer.OPTIMIZED)

      if product_optimized:
        num_of_products_optimized += 1

    return optimization_result_counts.OptimizationResultCounts(
        num_of_products_optimized, num_of_products_excluded)

  def _process_images_in_parallel(
      self, image_urls: Iterable[str]) -> List[image_download.ImageDownload]:
    """Processes all image URLs provided in parallel.

    File contents are stored in the resulting ImageDownload objects if the
    download is successful, or a flag indicating an error if not.

    Args:
      image_urls: List of image URLs to process.

    Returns:
      List of ImageDownload objects populated with either image contents or
      a flag indicating a response error.
    """
    images = [image_download.ImageDownload(
        image_invalid=False, score=float('inf'), original_index=index, url=url)
              for index, url in enumerate(image_urls)]

    num_threads = min(len(image_urls), self._max_available_threads)
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=num_threads,
        thread_name_prefix=_THREAD_NAME_PREFIX
        ) as thread_executor:

      images_futures = {thread_executor.submit(self._process_single_image,
                                               image): image
                        for image in images}

      for future in concurrent.futures.as_completed(images_futures):
        future.add_done_callback(_log_download_status)

      concurrent.futures.wait(images_futures,
                              return_when=concurrent.futures.ALL_COMPLETED)
    return images

  def _process_single_image(self,
                            image: image_download.ImageDownload
                            ) -> image_download.ImageDownload:
    """Processes the file indicated in the provided ImageDownload.

    Processing consists of multiple steps performed in sequence:
      1) Validate URL formatting.
      2) If self.require_image_can_be_downloaded = True, download the image and
          perform checks on image file content.
      3) If self.require_image_score_quality_better_than is finite, score
          the downloaded image using a model.

    Mutates the ImageDownload provided as the image parameter
    (sets `content`, `image_invalid`, and `score` attributes) according to:

      * `content` is filled with image file content if the URL is valid,
        excepting any network errors.
      * `image_invalid` is set to True if any of the following criteria are met:
        - The URL does not meet the criteria for image_link at
          https://support.google.com/merchants/answer/7052112.
        - The image is larger than 16MB.
        - The image cannot be downloaded due to a networking error.
      * score is a number, where lower numbers represent higher quality images.

    Args:
      image: The file to download and score.

    Returns:
      A mutated version of the image parameter containing the file content if
      the download was successful, and a flag indicating if there is anything
      that would cause the image to be invalid.
    """
    if not url_util.is_valid_image_url(image.url,
                                       constants.MAX_IMAGE_URL_LENGTH):
      image.image_invalid = True
      logging.info('Image at `%s` is invalid (URL is not valid).', image.url)
      return image

    if not self.require_image_can_be_downloaded:
      return image

    try:
      image.content = networking.load_bytes_at_url(image.url)
    except urllib.error.URLError:
      image.image_invalid = True
      logging.info('Image at `%s` is invalid (could not reach URL).', image.url)
      return image

    image_memory_size = sys.getsizeof(image.content)
    if image_memory_size > constants.MAX_IMAGE_FILE_SIZE_BYTES:
      image.image_invalid = True
      logging.info('Image at `%s` is invalid (%s bytes is larger than the'
                   ' maximum %s bytes).',
                   image.url,
                   image_memory_size,
                   constants.MAX_IMAGE_FILE_SIZE_BYTES)
      return image

    if math.isinf(self.require_image_score_quality_better_than):
      return image

    if image.content:
      image.score = image_util.score_image(image.content)
      if image.score > self.require_image_score_quality_better_than:
        image.image_invalid = True
      logging.debug('Scored image at `%s`; score=`%s`', image.url, image.score)

    return image


def _log_download_status(future: concurrent.futures.Future) -> None:
  """Logs information regarding the success of an asynchronous file download.

  Args:
    future: Resolved future containing an ImageDownload from the HTTP response.
  """
  image = future.result()
  if image.image_invalid:
    logging.debug('Could not resolve file `%s`.', image.url)
  else:
    logging.debug('Resolved `%s` (%s bytes).',
                  image.url, sys.getsizeof(image.content))


def _truncate_excess_images(images: List[image_download.ImageDownload]
                            ) -> Tuple[List[image_download.ImageDownload], int]:
  """Truncates the list of ImageDownloads to the maximum length allowed.

  First, removes any images with errors, starting from the end of the list.
  Next removes images by index, starting from the end of the list as needed.
  Consistently starts from the end of the list to preferentially preserve the
  first elements of the array (compared with those at the end) since a typical
  product has images in decreasing order of importance.

  Only truncates enough images to meet the MAX_ALTERNATE_IMAGE_URLS length
  requirement.
  Mutates the list of images provided as a parameter
  (removes some images from the list).

  Args:
    images: Downloaded images or errors, stored as ImageDownload objects.

  Returns:
    A tuple of the updated images and the number of images removed.
  """
  num_to_remove = max(0, len(images) - constants.MAX_ALTERNATE_IMAGE_URLS)

  reversed_images = list(reversed(images))
  for image in reversed_images:
    if len(images) <= constants.MAX_ALTERNATE_IMAGE_URLS:
      break
    if image.image_invalid:
      logging.debug('Removing excess additionalImageLink due to download error:'
                    ' Removing `%s`.', image.url)
      images.remove(image)

  # Removes any remaining images if `images` is still longer than the maximum.
  images = images[:constants.MAX_ALTERNATE_IMAGE_URLS]
  return (images, num_to_remove)


def _swap_original_image_with_best_alternative(
    product: Mapping[str, Any],
    original_image: image_download.ImageDownload,
    alternative_images: Iterable[image_download.ImageDownload]
    ) -> Mapping[str, Any]:
  """Swaps the original imageLink URL with the URL of the best alternate.

  Mutates the product provided as a parameter
  (swaps the imageLink URL with one of the additionalImageLink URLs).

  Args:
    product: The product to optimize.
    original_image: Downloaded image (imageLink URL) or error.
    alternative_images: Downloaded images (from additionalImageLink URLs) or
        errors, stored as ImageDownload objects.

  Returns:
    The product parameter, mutated such that the original imageLink URL is
    swapped with an alternative from the available additionalImageLinks.
  """

  # ImageDownload has attributes in priority order, so sorting finds the "best"
  best_images = sorted(x for x in alternative_images if not x.image_invalid)

  product['imageLink'] = best_images[0].url

  best_alternative_image_index = product[
      'additionalImageLink'].index(best_images[0].url)
  product['additionalImageLink'][
      best_alternative_image_index] = original_image.url

  logging.info('Swapped primary image with additional image link at index=%s.',
               best_alternative_image_index)

  return product
