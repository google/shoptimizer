# coding=utf-8
# Copyright 2026 Google LLC.
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


import unittest

from util import api_adapter


class ApiAdapterTest(unittest.TestCase):
  """Unit tests for ApiAdapter translating between v1 and v2 payloads."""

  def test_translate_v2_to_v1_success(self) -> None:
    v2_payload = {
        'entries': [{
            'batchId': 101,
            'merchantId': 9876543,
            'method': 'insert',
            'dataSource': 'accounts/9876543/dataSources/55555',
            'productInput': {
                'offerId': 'sku_valid_item',
                'contentLanguage': 'en',
                'feedLabel': 'US',
                'channel': 'ONLINE',
                'productAttributes': {
                    'title': 'Clean Cotton T-Shirt',
                    'description': 'A high quality shirt.',
                    'gtins': ['0001234567890'],
                    'mpn': 'TS-100',
                    'price': {
                        'amountMicros': '29990000',
                        'currencyCode': 'USD',
                    },
                },
            },
        }]
    }

    expected_v1_payload = {
        'entries': [{
            'batchId': 101,
            'merchantId': 9876543,
            'method': 'insert',
            'dataSource': 'accounts/9876543/dataSources/55555',
            'product': {
                'offerId': 'sku_valid_item',
                'contentLanguage': 'en',
                'targetCountry': 'US',
                'channel': 'ONLINE',
                'title': 'Clean Cotton T-Shirt',
                'description': 'A high quality shirt.',
                'gtin': '0001234567890',
                'mpn': 'TS-100',
                'price': {'value': '29.99', 'currency': 'USD'},
            },
        }]
    }

    result = api_adapter.translate_v2_to_v1(v2_payload)
    self.assertEqual(result, expected_v1_payload)

  def test_translate_v2_to_v1_with_attributes_fallback(self) -> None:
    v2_payload = {
        'entries': [{
            'batchId': 101,
            'productInput': {
                'offerId': 'sku_valid_item',
                'contentLanguage': 'en',
                'feedLabel': 'US',
                'channel': 'ONLINE',
                'attributes': {
                    'title': 'Clean Cotton T-Shirt',
                },
            },
        }]
    }

    expected_v1_payload = {
        'entries': [{
            'batchId': 101,
            'product': {
                'offerId': 'sku_valid_item',
                'contentLanguage': 'en',
                'targetCountry': 'US',
                'channel': 'ONLINE',
                'title': 'Clean Cotton T-Shirt',
            },
        }]
    }

    result = api_adapter.translate_v2_to_v1(v2_payload)
    self.assertEqual(result, expected_v1_payload)

  def test_translate_v2_to_v1_multiple_gtins(self) -> None:
    v2_payload = {
        'entries': [{
            'productInput': {
                'productAttributes': {
                    'gtins': ['123', '456', '789'],
                }
            }
        }]
    }

    result = api_adapter.translate_v2_to_v1(v2_payload)
    self.assertEqual(result['entries'][0]['product']['gtin'], '123,456,789')

  def test_translate_v2_to_v1_empty_gtins(self) -> None:
    v2_payload = {
        'entries': [
            {
                'productInput': {
                    'productAttributes': {
                        'gtins': [],
                    }
                }
            }
        ]
    }

    result = api_adapter.translate_v2_to_v1(v2_payload)
    self.assertEqual(result['entries'][0]['product']['gtin'], '')

  def test_translate_v1_to_v2_success(self) -> None:
    v1_payload = {
        'error-msg': 'test error',
        'optimization-results': {'title-optimizer': {'optimized': 1}},
        'plugin-results': {},
        'optimized-data': {
            'entries': [{
                'batchId': 101,
                'merchantId': 9876543,
                'method': 'insert',
                'product': {
                    'offerId': 'sku_valid_item',
                    'contentLanguage': 'en',
                    'targetCountry': 'US',
                    'channel': 'ONLINE',
                    'title': 'Clean Cotton T-Shirt (Optimized)',
                    'description': 'A high quality shirt.',
                    'gtin': '0001234567890',
                    'mpn': 'TS-100',
                    'price': {'value': '29.99', 'currency': 'USD'},
                },
            }]
        },
    }

    original_v2_payload = {
        'entries': [{
            'batchId': 101,
            'merchantId': 9876543,
            'method': 'insert',
            'productInput': {
                'offerId': 'sku_valid_item',
                'contentLanguage': 'en',
                'feedLabel': 'US',
                'channel': 'ONLINE',
                'productAttributes': {
                    'title': 'Clean Cotton T-Shirt',
                    'description': 'A high quality shirt.',
                    'gtins': ['0001234567890'],
                    'mpn': 'TS-100',
                    'price': {
                        'amountMicros': '29990000',
                        'currencyCode': 'USD',
                    },
                },
            },
        }]
    }

    expected_v2_payload = {
        'error-msg': 'test error',
        'optimization-results': {'title-optimizer': {'optimized': 1}},
        'plugin-results': {},
        'optimized-data': {
            'entries': [{
                'batchId': 101,
                'merchantId': 9876543,
                'method': 'insert',
                'productInput': {
                    'offerId': 'sku_valid_item',
                    'contentLanguage': 'en',
                    'feedLabel': 'US',
                    'channel': 'ONLINE',
                    'productAttributes': {
                        'title': 'Clean Cotton T-Shirt (Optimized)',
                        'description': 'A high quality shirt.',
                        'gtins': ['0001234567890'],
                        'mpn': 'TS-100',
                        'price': {
                            'amountMicros': '29990000',
                            'currencyCode': 'USD',
                        },
                    },
                },
            }]
        },
    }

    result = api_adapter.translate_v1_to_v2(v1_payload, original_v2_payload)
    self.assertEqual(result, expected_v2_payload)

  def test_translate_v1_to_v2_multiple_gtins(self) -> None:
    v1_payload = {
        'optimized-data': {
            'entries': [
                {
                    'product': {
                        'gtin': '123,456,789',
                    }
                }
            ]
        }
    }
    original_v2_payload = {'entries': [{'productInput': {}}]}

    result = api_adapter.translate_v1_to_v2(v1_payload, original_v2_payload)
    self.assertEqual(
        result['optimized-data']['entries'][0]['productInput'][
            'productAttributes'
        ]['gtins'],
        ['123', '456', '789'],
    )

  def test_translate_v2_to_v1_advanced_types(self) -> None:
    v2_payload = {
        'entries': [{
            'productInput': {
                'productAttributes': {
                    'size': 'XL',
                    'price': {
                        'amountMicros': '29990000',
                        'currencyCode': 'USD',
                    },
                    'salePrice': {
                        'amountMicros': '19990000',
                        'currencyCode': 'USD',
                    },
                    'shipping': [{
                        'price': {
                            'amountMicros': '5000000',
                            'currencyCode': 'USD',
                        },
                        'country': 'US',
                        'minHandlingTime': '2',
                        'maxHandlingTime': '5',
                    }],
                }
            }
        }]
    }

    expected_v1_payload = {
        'entries': [{
            'product': {
                'sizes': ['XL'],
                'price': {'value': '29.99', 'currency': 'USD'},
                'salePrice': {'value': '19.99', 'currency': 'USD'},
                'shipping': [{
                    'price': {'value': '5', 'currency': 'USD'},
                    'country': 'US',
                    'minHandlingTime': 2,
                    'maxHandlingTime': 5,
                }],
            }
        }]
    }

    result = api_adapter.translate_v2_to_v1(v2_payload)
    self.assertEqual(result, expected_v1_payload)

  def test_translate_v1_to_v2_advanced_types(self) -> None:
    v1_payload = {
        'optimized-data': {
            'entries': [{
                'product': {
                    'sizes': ['XL'],
                    'price': {'value': '29.99', 'currency': 'USD'},
                    'salePrice': {'value': '19.99', 'currency': 'USD'},
                    'shipping': [{
                        'price': {'value': '5.00', 'currency': 'USD'},
                        'country': 'US',
                        'minHandlingTime': 2,
                        'maxHandlingTime': 5,
                    }],
                }
            }]
        }
    }

    original_v2_payload = {
        'entries': [{
            'productInput': {
                'productAttributes': {
                    'size': 'XL',
                    'price': {
                        'amountMicros': '29990000',
                        'currencyCode': 'USD',
                    },
                    'salePrice': {
                        'amountMicros': '19990000',
                        'currencyCode': 'USD',
                    },
                    'shipping': [{
                        'price': {
                            'amountMicros': '5000000',
                            'currencyCode': 'USD',
                        },
                        'country': 'US',
                        'minHandlingTime': '2',
                        'maxHandlingTime': '5',
                    }],
                }
            }
        }]
    }

    expected_v2_payload = {
        'error-msg': '',
        'optimization-results': {},
        'plugin-results': {},
        'optimized-data': {
            'entries': [{
                'productInput': {
                    'productAttributes': {
                        'size': 'XL',
                        'price': {
                            'amountMicros': '29990000',
                            'currencyCode': 'USD',
                        },
                        'salePrice': {
                            'amountMicros': '19990000',
                            'currencyCode': 'USD',
                        },
                        'shipping': [{
                            'price': {
                                'amountMicros': '5000000',
                                'currencyCode': 'USD',
                            },
                            'country': 'US',
                            'minHandlingTime': '2',
                            'maxHandlingTime': '5',
                        }],
                    }
                }
            }]
        },
    }

    result = api_adapter.translate_v1_to_v2(v1_payload, original_v2_payload)
    self.assertEqual(result, expected_v2_payload)


if __name__ == '__main__':
  unittest.main()
