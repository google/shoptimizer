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

"""The base optimizer that all optimizers must inherit from."""
import _pickle as pickle
import abc
import logging
import os
from typing import Any, Dict

import constants
import enums
from models import optimization_result
import original_types

# final was moved from typing_extensions to typing in Python 3.8 per:
# https://mypy.readthedocs.io/en/stable/final_attrs.html
#

try:
  from typing import final
except ImportError:
  from typing_extensions import final



OPTIMIZED = enums.TrackingTag.OPTIMIZED
SANITIZED = enums.TrackingTag.SANITIZED
SANITIZED_AND_OPTIMIZED = enums.TrackingTag.SANITIZED_AND_OPTIMIZED


class BaseOptimizer(abc.ABC):
  """The base optimizer that all optimizers must inherit from.

  Usage example:

    class ExampleOptimizer(base_optimizer.BaseOptimizer):
      # The URL parameter to call your optimizer
      # Ex: {host}/shoptimizer/v1/batch/optimize?example-optimizer=true
      _OPTIMIZER_PARAMETER = 'example-optimizer'

      def _optimize(self, data: Dict[str, Any]) -> int:
        # Entry point for optimization logic.
        num_of_products_optimized = 0
        num_of_products_excluded = 0

        for entry in data['entries']:
          product = entry['product']
          product['unoptimized-field'] = 'optimized-value'  # Fixes the data.
          num_of_products_optimized = num_of_products_optimized + 1
          base_optimizer.set_optimization_tracking(
            entry,  base_optimizer.OPTIMIZED)

        return optimization_result_counts.OptimizationResultCounts(
          num_of_products_optimized, num_of_products_excluded)

  See also identity_optimizer.py and my_plugin.py for example implementations.
  """

  _OPTIMIZER_PARAMETER: str

  def __init__(self,
               mined_attributes: original_types.MinedAttributes = None) -> None:
    """Initializes BaseOptimizer.

    Args:
      mined_attributes: A list of mined attributes mapped to product ids.
    """
    super(BaseOptimizer, self).__init__()
    self._mined_attributes = mined_attributes

  @final
  @property
  def optimizer_parameter(self) -> str:
    """The URL parameter that indicates this optimizer should be run."""
    try:
      return self._OPTIMIZER_PARAMETER
    except AttributeError:
      raise NotImplementedError(
          'Optimizer must implement a str property called "_OPTIMIZER_PARAMETER"'
      )

  @final
  def process(
      self,
      product_batch: Dict[str, Any],
      language: str = constants.DEFAULT_LANG,
      country: str = constants.DEFAULT_COUNTRY,
      currency: str = constants.DEFAULT_CURRENCY
  ) -> (Dict[str, Any], optimization_result.OptimizationResult):
    """The entry point for running optimization processing.

    Args:
      product_batch:  A batch of product data.
      language: The language this optimizer uses. Default is English ("en") as
        per ISO 639-2 Language codes.
      country: The country this optimizer uses.
      currency: The currency this optimizer uses.

    Returns:
      The optimized product data: Dict[str, Any]
      The results of this optimization: optimization_result.OptimizationResult
    """
    optimized_product_batch = pickle.loads(pickle.dumps(product_batch))

    try:
      optimizer_result_counts = self._optimize(optimized_product_batch,
                                               language, country, currency)
    except NotImplementedError:
      logging.error('Optimizer %s did not implement base_optimizer correctly.',
                    self._OPTIMIZER_PARAMETER)
      raise
    # As per PyStyle, Exception is caught to create an isolation point
    # that protects the main API container from crashing, so
    
    except Exception as error:
      logging.exception('Error while running optimization %s: %s',
                        self._OPTIMIZER_PARAMETER, error)
      return product_batch, optimization_result.OptimizationResult(
          'failure', 0, str(error))
    else:
      logging.info(
          'Finished running optimizer: %s. %s products were touched by the '
          'optimizer and %s products were requested to be excluded from being '
          'run by this optimizer.', self._OPTIMIZER_PARAMETER,
          optimizer_result_counts.num_of_products_optimized,
          optimizer_result_counts.num_of_products_excluded)
      return optimized_product_batch, optimization_result.OptimizationResult(
          'success', optimizer_result_counts.num_of_products_optimized, '')

  @abc.abstractmethod
  def _optimize(self, product_batch: Dict[str, Any], language: str,
                country: str, currency: str) -> int:
    """Implement optimization logic in this method.

    Subclasses must call base_optimizer.set_optimization_tracking(...)
    to track optimized products in Google Ads.

    Args:
      product_batch:  A batch of product data.
      language: The language to use for this optimizer.
      country: The country to use for this optimizer.
      currency: The currency to use for this optimizer.

    Returns:
      The number of products affected and excluded by this optimization:
        OptimizationResultCounts
    """
    raise NotImplementedError('Optimizer must implement the method optimize.')

  def get_optimizer_parameter(self) -> str:
    """Returns the URL parameter that indicates this optimizer should be run."""
    return self._OPTIMIZER_PARAMETER


def set_optimization_tracking(product: Dict[str, Any],
                              tracking_tag: enums.TrackingTag) -> None:
  """Marks a product as optimized so it can be tracked in Google Ads.

  If the current tracking value is already 'sanitized' and an 'optimized' tag
  is supplied, or vice versa, the value will be updated to 'sanitized-optimized'
  to indicate that the product has been both sanitized and optimized.

  Args:
    product:  A dictionary representing a product resource.
    tracking_tag: The tag to use to track this product.
  """
  product_tracking_field = os.environ.get('PRODUCT_TRACKING_FIELD')

  if not product_tracking_field:
    # Client does not want to perform item tracking (tracking env var empty)
    return

  if not product_tracking_field.startswith('customLabel'):
    logging.error(
        'Failed to set product tracking. '
        'Product tracking field is not a custom label: %s',
        product_tracking_field)
    return

  product_tracking_value = product.get(product_tracking_field, '')

  if not product_tracking_value:
    product[product_tracking_field] = tracking_tag.value
    return

  # Product has been sanitized and optimized.
  both = SANITIZED_AND_OPTIMIZED.value
  if product_tracking_value == SANITIZED.value and tracking_tag == OPTIMIZED:
    product[product_tracking_field] = both
  elif product_tracking_value == OPTIMIZED.value and tracking_tag == SANITIZED:
    product[product_tracking_field] = both
