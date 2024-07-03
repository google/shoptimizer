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

"""Unit tests for main.py."""
import base64
import http
import json
import unittest

from absl.testing import parameterized

import main
from test_data import requests_bodies


class MainTest(parameterized.TestCase):

  def setUp(self) -> None:
    super(MainTest, self).setUp()
    main.app.testing = True
    self.test_client = main.app.test_client()

  def test_health(self):
    response = self.test_client.get(f'{main._V1_BASE_URL}/health')
    response_data = response.data.decode('utf-8')

    self.assertEqual('Success', response_data)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  # region bad request tests
  def test_non_valid_json_request_returns_error(self):
    non_json_request_body = requests_bodies.INVALID_NON_JSON

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize', data=non_json_request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)

    self.assertEqual('Request must be valid JSON', response_dict['error-msg'])
    self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)

  def test_entries_missing_in_request_returns_error(self):
    request_body_missing_entries = requests_bodies.INVALID_MISSING_ENTRIES

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize',
        json=request_body_missing_entries)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)

    self.assertEqual('Request must contain entries as a key.',
                     response_dict['error-msg'])
    self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)

  def test_entries_with_no_list_of_products_returns_error(self):
    request_body_missing_entries_product_list = requests_bodies.INVALID_ENTRIES_MISSING_PRODUCT_LIST
    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize',
        json=request_body_missing_entries_product_list)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)

    self.assertEqual('Entries must contain a list of products.',
                     response_dict['error-msg'])
    self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)

  @parameterized.named_parameters([{
      'testcase_name': 'title_is_numeric',
      'attribute': 'title'
  }, {
      'testcase_name': 'description_is_numeric',
      'attribute': 'description'
  }])
  def test_numeric_attribute_is_converted_to_string(self, attribute):
    request_body = requests_bodies.build_request_body(
        properties_to_be_updated={attribute: 1.234})

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize', json=request_body)

    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)

    self.assertIsInstance(
        response_dict['optimized-data']['entries'][0]['product'][attribute],
        str)

  def test_unmapped_route_returns_404(self):
    response = self.test_client.get(f'{main._V1_BASE_URL}/unmapped-route')
    self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)

  def test_invalid_query_string_param_returns_bad_request(self):
    request_body = requests_bodies.build_request_body()

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?invalid-parameter=true',
        json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)

    self.assertEqual(
        ('Invalid query string parameter detected. Please provide a valid '
         'Shoptimizer API query string parameter.'), response_dict['error-msg'])
    self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)

  # endregion

  # region builtin optimizer tests

  def test_optimizer_run_when_parameter_set_to_true(self):
    request_body = requests_bodies.build_request_body()

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?identity-optimizer=true',
        json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['optimization-results']

    self.assertIn('identity-optimizer', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_optimizers_run_in_the_same_order_as_query_string(self):
    request_body = requests_bodies.build_request_body()
    optimizers_to_execute = [
        'identity-optimizer', 'adult-optimizer', 'title-optimizer'
    ]
    query_string = '?' + '=true&'.join(optimizers_to_execute) + '=true'

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize{query_string}', json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['optimization-results']
    optimizers_executed = list(optimization_results.keys())
    self.assertEqual(optimizers_to_execute, optimizers_executed)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_title_word_order_optimizer_runs_at_the_end_regardless_of_the_order_of_query_string(
      self):
    request_body = requests_bodies.build_request_body()
    optimizers_to_execute = [
        'identity-optimizer', 'title-word-order-optimizer', 'title-optimizer'
    ]
    query_string = '?' + '=true&'.join(optimizers_to_execute) + '=true'

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize{query_string}', json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['optimization-results']

    optimizers_executed = list(optimization_results.keys())
    self.assertEqual('title-word-order-optimizer', optimizers_executed[-1])
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_optimizer_config_override_overwrites_default_optimizer(self):
    request_body = requests_bodies.build_request_body(
        properties_to_be_updated={'productTypes': 'ビール・洋酒'})
    optimizers_to_execute = ['adult-optimizer']
    query_string = '?' + '=true&'.join(optimizers_to_execute) + '=true'
    override_config_contents_raw = b"""
      {
        "adult_product_types": [
          "no match",
        ],
        "adult_google_product_categories": {
          "no match": [
            "*",
          ]
        }
      }
    """
    override_config_contents_base64 = (
        base64.b64encode(override_config_contents_raw))
    override_config_header = ({
        'adult_optimizer_config_override': override_config_contents_base64
    })
    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize{query_string}',
        json=request_body,
        headers=override_config_header)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['optimization-results']

    optimizers_executed = list(optimization_results.keys())
    self.assertEqual(optimizers_to_execute, optimizers_executed)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)
    self.assertNotIn('adult-optimization', optimization_results)

  def test_optimizer_not_run_when_parameter_set_to_false(self):
    request_body = requests_bodies.build_request_body()

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?identity-optimizer=false',
        json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['optimization-results']

    self.assertNotIn('identity-optimization', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_optimizer_not_run_when_parameter_missing(self):
    request_body = requests_bodies.build_request_body()

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize', json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['optimization-results']

    self.assertNotIn('identity-optimization', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  # endregion

  # region plugin optimizer tests
  def test_plugin_run_when_parameter_set_to_true(self):
    request_body = requests_bodies.build_request_body()

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?my-plugin=true', json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['plugin-results']

    self.assertIn('my-plugin', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_plugin_not_run_when_parameter_set_to_false(self):
    request_body = requests_bodies.build_request_body()

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?my-plugin=false',
        json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['plugin-results']

    self.assertNotIn('my-plugin', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_plugin_not_run_when_parameter_missing(self):
    request_body = requests_bodies.build_request_body()

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize', json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['plugin-results']

    self.assertNotIn('my-plugin', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  # endregion

  # region excluded optimizer tests
  def test_optimizers_not_run_when_excluded(self):
    max_title_length = 150
    original_title = 'a' * (max_title_length * 2)
    request_body = requests_bodies.build_request_body(
        properties_to_be_updated={'title': original_title})

    query_string_params = 'title-length-optimizer=true'

    response_without_exclusion = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?{query_string_params}',
        json=request_body)
    response_without_exclusion_data = response_without_exclusion.data.decode(
        'utf-8')
    response_without_exclusion_dict = json.loads(
        response_without_exclusion_data)
    optimization_without_exclusion_results = response_without_exclusion_dict[
        'optimization-results']

    exclude_optimizers = ['title-length-optimizer']
    request_body['entries'][0]['excludeOptimizers'] = exclude_optimizers
    response_with_exclusion = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?{query_string_params}',
        json=request_body)
    response_with_exclusion_data = response_with_exclusion.data.decode('utf-8')
    response_with_exclusion_dict = json.loads(response_with_exclusion_data)
    optimization_with_exclusion_results = response_with_exclusion_dict[
        'optimization-results']
    title_from_excluded_response = response_with_exclusion_dict[
        'optimized-data']['entries'][0]['product']['title']

    self.assertEqual(
        1,
        optimization_without_exclusion_results.get(
            'title-length-optimizer').get('num_of_products_optimized'))
    self.assertEqual(
        0,
        optimization_with_exclusion_results.get('title-length-optimizer').get(
            'num_of_products_optimized'))
    self.assertEqual(original_title, title_from_excluded_response)

  def test_excluded_optimizers_attribute_removed_in_response(self):
    max_title_length = 150
    request_body = requests_bodies.build_request_body(
        properties_to_be_updated={'title': 'a' * (max_title_length * 2)})

    query_string_params = 'title-length-optimizer=true'

    exclude_optimizers = ['title-length-optimizer']

    request_body['entries'][0]['excludeOptimizers'] = exclude_optimizers
    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?{query_string_params}',
        json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    self.assertIsNone(
        response_dict['optimized-data']['entries'][0].get('excludedOptimizers'))

  # endregion

if __name__ == '__main__':
  unittest.main()
