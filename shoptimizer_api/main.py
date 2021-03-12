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

# python3
"""Defines the Flask routes (API endpoints) for the Shoptimizer API.

This module acts as the main entry point to the Shoptimizer API.
"""

import copy
import http

import logging
import sys
from typing import Any, Dict, List, Sequence, Tuple

import flask

import constants
from models import optimization_result
from optimizers_utils import optimizer_cache
import original_types
from util import app_util
from util import attribute_miner

_V1_BASE_URL = '/shoptimizer/v1'
_OPTIMIZERS_BUILTIN_PACKAGE = 'optimizers_builtin'
_OPTIMIZERS_PLUGINS_PACKAGE = 'optimizers_plugins'
_OPTIMIZERS_THAT_USE_MINED_ATTRIBUTES = frozenset(
    ['title-optimizer', 'description-optimizer'])
_OPTIMIZERS_TO_RUN_LAST = ('title-word-order-optimizer',)
_SUPPORTED_LANGUAGES = frozenset(['en', 'ja'])
_LANG_QUERY_STRING_KEY = 'lang'
_COUNTRY_QUERY_STRING_KEY = 'country'
_CURRENCY_QUERY_STRING_KEY = 'currency'

# Sets logging to debug to show logging.info messages.
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

_builtin_optimizer_cache = optimizer_cache.OptimizerCache(
    _OPTIMIZERS_BUILTIN_PACKAGE)
_plugin_optimizer_cache = optimizer_cache.OptimizerCache(
    _OPTIMIZERS_PLUGINS_PACKAGE)

_BUILTIN_OPTIMIZER_PARAMETERS = [
    optimizer_class.get_optimizer_parameter(optimizer_class)
    for optimizer_class in _builtin_optimizer_cache.optimizer_classes
]
_PLUGIN_OPTIMIZER_PARAMETERS = [
    optimizer_class.get_optimizer_parameter(optimizer_class)
    for optimizer_class in _plugin_optimizer_cache.optimizer_classes
]
_VALID_OPTIMIZER_PARAMETERS = _BUILTIN_OPTIMIZER_PARAMETERS + _PLUGIN_OPTIMIZER_PARAMETERS

app = app_util.create_app()


@app.route(f'{_V1_BASE_URL}/batch/optimize', methods=['POST'])
def optimize() -> Tuple[str, http.HTTPStatus]:
  """Optimizes a JSON payload containing product data.

  The request body format should match the Content API custom batch insert
  request format:
  https://developers.google.com/shopping-content/v2/reference/v2/products/custombatch
  {
    "entries": [
      {
        "batchId": unsigned integer,
        "merchantId": unsigned long,
        "method": string,
        "productId": string,
        "product": products Resource
      }
    ]
  }

  The API does not mirror Content API for Shopping quota limits, so you may send
  as much data in a batch as your host server is configured to handle.

  The response contains a JSON string of optimization results and an HTTP status
  code.

  Optimization results:
  - optimized-data: The optimized product data. Can be sent to Content API.
  - optimization-results: A result summary for each builtin optimizer
    (num of products optimized, errors encountered, etc.).
  - plugin-results: A result summary for each user-built optimizer
    (num of products optimized, errors encountered, etc.).

  HTTP status code:
  - 200: The request was successfully processed.
  - 400: The request was invalid and failed to be processed.

  Returns:
    JSON string and HTTP status code.
  """
  lang_url_parameter = flask.request.args.get('lang',
                                              constants.DEFAULT_LANG).lower()
  country_url_parameter = flask.request.args.get(
      'country', constants.DEFAULT_COUNTRY).lower()
  currency_url_parameter = flask.request.args.get(
      'currency', constants.DEFAULT_CURRENCY).upper()
  request_valid, error_msg = _check_request_valid(lang_url_parameter)

  if not request_valid:
    response_dict = _build_response_dict({}, {}, {}, error_msg)
    return flask.make_response(
        flask.jsonify(response_dict), http.HTTPStatus.BAD_REQUEST)

  product_batch = flask.request.json

  optimized_product_batch, builtin_optimizer_results = _run_optimizers(
      product_batch, lang_url_parameter, country_url_parameter,
      currency_url_parameter, _builtin_optimizer_cache)
  optimized_product_batch, plugin_optimizer_results = _run_optimizers(
      optimized_product_batch, lang_url_parameter, country_url_parameter,
      currency_url_parameter, _plugin_optimizer_cache)

  response_dict = _build_response_dict(optimized_product_batch,
                                       builtin_optimizer_results,
                                       plugin_optimizer_results)

  return flask.make_response(flask.jsonify(response_dict), http.HTTPStatus.OK)


def _check_request_valid(lang_url_parameter: str) -> (bool, str):
  """Checks that the flask request is in a valid format to be processed.

  Args:
    lang_url_parameter: The value, if supplied, of the "lang" url parameter.

  Returns:
    True if the request is valid, False otherwise: bool
    An error message describing the problem with the request, an empty string
    otherwise: str
  """
  if not flask.request.json:
    logging.error('Request was not valid JSON. Request: %s', flask.request.data)
    return False, 'Request must be valid JSON'

  if 'entries' not in flask.request.json:
    logging.error('Request did not contain entries key. Request: %s',
                  flask.request.json)
    return False, 'Request must contain entries as a key.'

  product_dict = flask.request.json

  if not isinstance(product_dict['entries'], list):
    logging.error('Entries did not contain a list of products. %s',
                  product_dict)
    return False, 'Entries must contain a list of products.'

  if lang_url_parameter not in _SUPPORTED_LANGUAGES:
    return False, (f'lang query parameter must be a supported language: '
                   f'{_SUPPORTED_LANGUAGES}')

  # Check for invalid query strings by comparing against optimizers.
  request_full_query_string_parameters = _extract_all_url_parameters()
  request_optimizer_query_string_parameters = set(
      request_full_query_string_parameters) - {
          _LANG_QUERY_STRING_KEY, _COUNTRY_QUERY_STRING_KEY,
          _CURRENCY_QUERY_STRING_KEY
      }
  invalid_query_string_parameters = list(
      request_optimizer_query_string_parameters -
      set(_VALID_OPTIMIZER_PARAMETERS))
  if invalid_query_string_parameters:
    logging.error('An invalid query string parameter was provided: %s',
                  invalid_query_string_parameters)
    return False, ('Invalid query string parameter detected. Please provide a '
                   'valid Shoptimizer API query string parameter.')

  return True, ''


def _run_optimizers(
    product_batch: Dict[str, Any],
    language: str,
    country: str,
    currency: str,
    cached_optimizers: optimizer_cache.OptimizerCache,
) -> (Dict[str, Any], Dict[str, optimization_result.OptimizationResult]):
  """Transforms a JSON payload of product data using optimizers.

  Args:
    product_batch: A batch of product data.
    language: The language to use for this request.
    country: The country to use for this request.
    currency: The currency to use for this request.
    cached_optimizers: A cache of optimizer classes.

  Returns:
    The optimized product batch: Dict[str, Any]
    The results of each optimizer run: Dict[str,
    optimization_result.OptimizationResult]
  """
  optimized_product_batch = copy.deepcopy(product_batch)
  optimization_results = {}

  mined_attributes = _get_mined_attributes(
      optimized_product_batch, language,
      country) if _mined_attributes_required() else {}

  optimizers = [
      optimizer_class(mined_attributes)
      for optimizer_class in cached_optimizers.optimizer_classes
  ]
  optimizer_parameters = [
      optimizer.optimizer_parameter for optimizer in optimizers
  ]
  optimizer_mapping = dict(zip(optimizer_parameters, optimizers))

  for optimizer_parameter in _generate_optimizer_parameter_list_to_run(
      optimizer_parameters_to_run_last=_OPTIMIZERS_TO_RUN_LAST):
    optimizer = optimizer_mapping.get(optimizer_parameter)
    if optimizer:
      logging.info(
          'Running optimization %s with language %s, country %s, currency %s',
          optimizer_parameter, language, country, currency)
      optimized_product_batch, result = optimizer.process(
          optimized_product_batch, language, country, currency)
      optimization_results[optimizer_parameter] = result

  return optimized_product_batch, optimization_results


def _mined_attributes_required() -> bool:
  """Returns True if mined attributes will be required for this batch.

  Returns:
    True if mined attributes will be required for the optimizers being run in
    this batch, false otherwise.
  """
  for optimizer_parameter in _OPTIMIZERS_THAT_USE_MINED_ATTRIBUTES:
    if _exists_in_query_string_with_value_true(optimizer_parameter):
      return True

  return False


def _exists_in_query_string_with_value_true(query_parameter_key: str) -> bool:
  """Checks if a given query parameter exists and is truthy.

  Args:
    query_parameter_key: Key of query parameter.

  Returns:
    Whether the query parameter has true value or not.
  """
  try:
    return flask.request.args.get(query_parameter_key, '').lower() == 'true'
  except RuntimeError as error:
    logging.exception('Error: Retrieving keys from Flask failed. %s', error)
    return False


def _get_mined_attributes(product_batch: Dict[str, Any], language: str,
                          country: str) -> original_types.MinedAttributes:
  """Gets a list of mined attributes for every product in the batch.

  Args:
    product_batch: A batch of product data.
    language: The language to use for this request.
    country: The country to use for this request.

  Returns:
    Mined attributes mapped to product ids in the batch.
  """
  miner = attribute_miner.AttributeMiner(language, country)
  return miner.mine_and_insert_attributes_for_batch(product_batch)


def _extract_all_url_parameters() -> List[str]:
  """Extracts all of the query string parameters from the request.

  Returns:
    A list of query string parameter keys.
  """
  try:
    return flask.request.args.keys() or []
  except RuntimeError as error:
    logging.exception('Error: Retrieving keys from Flask failed. %s', error)
    return []


def _generate_optimizer_parameter_list_to_run(
    optimizer_parameters_to_run_last: Sequence[str]) -> List[str]:
  """Generates a list of optimizer parameters whose values are true by extracting from query string.

  Also brings optimizer parameters that should run last to the end of the
  returning list.

  Args:
    optimizer_parameters_to_run_last: optimizer parameters that should run last.

  Returns:
    Optimizer parameters that exist in query string and are set to true.
  """
  optimizer_parameters: List[str] = []
  for parameter_key, parameter_value in flask.request.args.items():
    if isinstance(parameter_value, str) and parameter_value.lower() == 'true':
      optimizer_parameters.append(parameter_key)
  for optimizer_parameter_to_run_last in optimizer_parameters_to_run_last:
    if optimizer_parameter_to_run_last in optimizer_parameters:
      optimizer_parameters.remove(optimizer_parameter_to_run_last)
      optimizer_parameters.append(optimizer_parameter_to_run_last)
  return optimizer_parameters


def _build_response_dict(optimized_product_batch: Dict[str, Any],
                         builtin_optimizer_results: Dict[str, Any],
                         plugin_optimizer_results: Dict[str, Any],
                         error_msg: str = '') -> Dict[str, Any]:
  """Builds a dictionary of response data.

  Args:
    optimized_product_batch: A batch of optimized product data.
    builtin_optimizer_results: A list of builtin optimizers run.
    plugin_optimizer_results: A list of the user-built plugins run.
    error_msg (optional): Error messages related to top-level processing (for
      example, malformed requests).

  Returns:
    A response body with optimized product data.
  """
  response = {
      'optimized-data': optimized_product_batch,
      'optimization-results': builtin_optimizer_results,
      'plugin-results': plugin_optimizer_results
  }

  if error_msg:
    response['error-msg'] = error_msg

  return response


@app.route(f'{_V1_BASE_URL}/health', methods=['GET'])
def health() -> Tuple[str, http.HTTPStatus]:
  """A simple endpoint for checking the health of the deployed application.

  Returns:
    The string 'Success' and a 200 HTTP status code.
  """
  logging.info('Health called')
  return flask.make_response('Success', http.HTTPStatus.OK)


@app.errorhandler(404)
def not_found(_) -> Tuple[str, http.HTTPStatus]:
  return flask.make_response(
      flask.jsonify({'error': 'URL not found'}), http.HTTPStatus.NOT_FOUND)


if __name__ == '__main__':
  app.run()
