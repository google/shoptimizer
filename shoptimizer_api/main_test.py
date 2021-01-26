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
"""Unit tests for main.py."""
import http
import json

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

  def test_unmapped_route_returns_404(self):
    response = self.test_client.get(f'{main._V1_BASE_URL}/unmapped-route')
    self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)

  def test_invalid_query_string_param_returns_bad_request(self):
    request_body = requests_bodies.VALID_SINGLE_PRODUCT

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
    request_body = requests_bodies.VALID_SINGLE_PRODUCT

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?identity-optimizer=true',
        json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['optimization-results']

    self.assertIn('identity-optimizer', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_optimizers_run_in_the_same_order_as_query_string(self):
    request_body = requests_bodies.VALID_SINGLE_PRODUCT
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

  def test_optimizer_not_run_when_parameter_set_to_false(self):
    request_body = requests_bodies.VALID_SINGLE_PRODUCT

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?identity-optimizer=false',
        json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['optimization-results']

    self.assertNotIn('identity-optimization', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_optimizer_not_run_when_parameter_missing(self):
    request_body = requests_bodies.VALID_SINGLE_PRODUCT

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
    request_body = requests_bodies.VALID_SINGLE_PRODUCT

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?my-plugin=true', json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['plugin-results']

    self.assertIn('my-plugin', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_plugin_not_run_when_parameter_set_to_false(self):
    request_body = requests_bodies.VALID_SINGLE_PRODUCT

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize?my-plugin=false',
        json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['plugin-results']

    self.assertNotIn('my-plugin', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  def test_plugin_not_run_when_parameter_missing(self):
    request_body = requests_bodies.VALID_SINGLE_PRODUCT

    response = self.test_client.post(
        f'{main._V1_BASE_URL}/batch/optimize', json=request_body)
    response_data = response.data.decode('utf-8')
    response_dict = json.loads(response_data)
    optimization_results = response_dict['plugin-results']

    self.assertNotIn('my-plugin', optimization_results)
    self.assertEqual(http.HTTPStatus.OK, response.status_code)

  # endregion
