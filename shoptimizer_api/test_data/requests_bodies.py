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
"""Contains request bodies used for testing."""
import copy
import json
from typing import Any, Dict, List, Optional

VALID_SINGLE_PRODUCT = json.loads("""{
    "entries": [
        {
            "batchId": 1111,
            "merchantId": 1234567,
            "method": "insert",
            "product": {
                "kind": "content#product",
                "offerId": "1111111111",
                "source": "api",
                "title": "Google Tee",
                "description": "The Google Tee is available in ...",
                "link": "http://my.site.com/blacktee/",
                "imageLink": "https://shop.example.com/.../images/foo.jpg",
                "contentLanguage": "en",
                "targetCountry": "US",
                "channel": "online",
                "ageGroup": "adult",
                "availability": "in stock",
                "availabilityDate": "2019-01-25T13:00:00-08:00",
                "brand": "Google",
                "color": "black",
                "condition": "new",
                "customLabel0": "",
                "customLabel1": "",
                "customLabel2": "",
                "customLabel3": "",
                "customLabel4": "",
                "gender": "male",
                "googleProductCategory": "1604",
                "gtin": "608802531656",
                "itemGroupId": "google_tee",
                "identifierExists": true,
                "mpn": "608802531656",
                "price": {
                    "value": "21.99",
                    "currency": "USD"
                },
                "sizes": [
                    "Large"
                ],
                "destinations": [
                    {
                        "destinationName": "Shopping",
                        "intention": "required"
                    }
                ]
            }
        }
    ]
}""")

INVALID_NON_JSON = "'key': 'value'"

INVALID_MISSING_ENTRIES = json.loads("""{
            "batchId": 1111,
            "merchantId": 1234567,
            "method": "insert",
            "product": {
                "kind": "content#product",
                "offerId": "1111111111",
                "source": "api",
                "title": "Google Tee Black",
                "description": "The Black Google Tee is available in ...",
                "link": "http://my.site.com/blacktee/",
                "imageLink": "https://shop.example.com/.../images/foo.jpg",
                "contentLanguage": "en",
                "targetCountry": "US",
                "channel": "online",
                "ageGroup": "adult",
                "availability": "in stock",
                "availabilityDate": "2019-01-25T13:00:00-08:00",
                "brand": "Google",
                "color": "black",
                "condition": "new",
                "gender": "male",
                "googleProductCategory": "1604",
                "gtin": "608802531656",
                "itemGroupId": "google_tee",
                "mpn": "608802531656",
                "price": {
                    "value": "21.99",
                    "currency": "USD"
                },
                "sizes": [
                    "Large"
                ],
                "destinations": [
                    {
                        "destinationName": "Shopping",
                        "intention": "required"
                    }
                ]
            }
}""")

INVALID_ENTRIES_MISSING_PRODUCT_LIST = json.loads("""{
    "entries":
        {
            "batchId": 1111,
            "merchantId": 1234567,
            "method": "insert",
            "product": {
                "kind": "content#product",
                "offerId": "1111111111",
                "source": "api",
                "title": "Google Tee Black",
                "description": "The Black Google Tee is available in ...",
                "link": "http://my.site.com/blacktee/",
                "imageLink": "https://shop.example.com/.../images/foo.jpg",
                "contentLanguage": "en",
                "targetCountry": "US",
                "channel": "online",
                "ageGroup": "adult",
                "availability": "in stock",
                "availabilityDate": "2019-01-25T13:00:00-08:00",
                "brand": "Google",
                "color": "black",
                "condition": "new",
                "customLabel0": "",
                "customLabel1": "",
                "customLabel2": "",
                "customLabel3": "",
                "customLabel4": "",
                "gender": "male",
                "googleProductCategory": "1604",
                "gtin": "608802531656",
                "itemGroupId": "google_tee",
                "mpn": "608802531656",
                "price": {
                    "value": "21.99",
                    "currency": "USD"
                },
                "sizes": [
                    "Large"
                ],
                "destinations": [
                    {
                        "destinationName": "Shopping",
                        "intention": "required"
                    }
                ]
            }
        }
}""")


def build_request_body(
    properties_to_be_updated: Optional[Dict[str, Any]] = None,
    properties_to_be_removed: Optional[List[str]] = None) -> Dict[str, Any]:
  """Builds a dummy request body of 1 product.

  This function creates a request body from VALID_SINGLE_PRODUCT by
  updating/removing given properties.

  Args:
    properties_to_be_updated: The properties of a product and their values to be
      updated in a request body.
    properties_to_be_removed: The properties of a product that should be
      removed.

  Returns:
    A dummy request body of 1 product.
  """
  body = copy.deepcopy(VALID_SINGLE_PRODUCT)
  product = body['entries'][0]['product']

  if properties_to_be_updated:
    for key, value in properties_to_be_updated.items():
      product[key] = value

  if properties_to_be_removed:
    for key in properties_to_be_removed:
      if key in product:
        del product[key]

  return body
