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

"""Adapter utility translating between Merchant API (v2) and Content API (v1) schemas."""

from typing import Any

_METADATA_FIELDS = frozenset([
    'offerId',
    'contentLanguage',
    'channel',
    'targetCountry',
])


def _translate_v2_price_to_v1(v2_price: dict[str, Any]) -> dict[str, Any]:
  """Translates v2 Price (amountMicros, currencyCode) to v1 (value, currency)."""
  if not v2_price:
    return {}
  v1_price = {}
  amount_micros = v2_price.get('amountMicros')
  if amount_micros is not None:
    try:
      micros_val = int(amount_micros)
      float_val = micros_val / 1_000_000.0
      val_str = f'{float_val:.6f}'
      if '.' in val_str:
        val_str = val_str.rstrip('0').rstrip('.')
      v1_price['value'] = val_str
    except (ValueError, TypeError):
      v1_price['value'] = str(amount_micros)
  if 'currencyCode' in v2_price:
    v1_price['currency'] = v2_price['currencyCode']
  return v1_price


def _translate_v1_price_to_v2(v1_price: dict[str, Any]) -> dict[str, Any]:
  """Translates v1 Price (value, currency) to v2 (amountMicros, currencyCode)."""
  if not v1_price:
    return {}
  v2_price = {}
  value = v1_price.get('value')
  if value is not None:
    try:
      val = float(value)
      v2_price['amountMicros'] = str(int(round(val * 1_000_000)))
    except (ValueError, TypeError):
      v2_price['amountMicros'] = value
  if 'currency' in v1_price:
    v2_price['currencyCode'] = v1_price['currency']
  return v2_price


def _translate_v2_shipping_to_v1(
    v2_shipping: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  """Translates v2 shipping list to v1 format."""
  if not v2_shipping:
    return []
  v1_shipping = []
  for item in v2_shipping:
    v1_item = {}
    for k, v in item.items():
      if k == 'price':
        v1_item['price'] = _translate_v2_price_to_v1(v)
      elif k in (
          'minHandlingTime',
          'maxHandlingTime',
          'minTransitTime',
          'maxTransitTime',
      ):
        if v is not None:
          try:
            v1_item[k] = int(v)
          except (ValueError, TypeError):
            v1_item[k] = v
      else:
        v1_item[k] = v
    v1_shipping.append(v1_item)
  return v1_shipping


def _translate_v1_shipping_to_v2(
    v1_shipping: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  """Translates v1 shipping list back to v2 format."""
  if not v1_shipping:
    return []
  v2_shipping = []
  for item in v1_shipping:
    v2_item = {}
    for k, v in item.items():
      if k == 'price':
        v2_item['price'] = _translate_v1_price_to_v2(v)
      elif k in (
          'minHandlingTime',
          'maxHandlingTime',
          'minTransitTime',
          'maxTransitTime',
      ):
        if v is not None:
          v2_item[k] = str(v)
      else:
        v2_item[k] = v
    v2_shipping.append(v2_item)
  return v2_shipping


def translate_v2_to_v1(v2_payload: dict[str, Any]) -> dict[str, Any]:
  """Translates a Merchant API (v2) payload to Content API (v1) format.

  Args:
    v2_payload: A dictionary representing the v2 payload.

  Returns:
    A dictionary representing the translated v1 payload.
  """
  v1_payload = {'entries': []}
  for v2_entry in v2_payload.get('entries', []):
    v1_entry = {}
    for k, v in v2_entry.items():
      if k != 'productInput':
        v1_entry[k] = v

    v2_product_input = v2_entry.get('productInput', {})
    v1_product = {}

    # Copy top-level metadata from productInput
    for field in ('offerId', 'contentLanguage', 'channel'):
      if field in v2_product_input:
        v1_product[field] = v2_product_input[field]

    # Mapping regionalization: feedLabel -> targetCountry
    if 'feedLabel' in v2_product_input:
      v1_product['targetCountry'] = v2_product_input['feedLabel']

    # Get attributes (checking both primary and fallback key names)
    v2_attributes = v2_product_input.get(
        'productAttributes', v2_product_input.get('attributes', {})
    )

    for field, val in v2_attributes.items():
      if field == 'gtins':
        if val is not None:
          v1_product['gtin'] = ','.join(str(g) for g in val)
      elif field == 'size':
        if val is not None:
          v1_product['sizes'] = val if isinstance(val, list) else [val]
      elif field in (
          'price',
          'salePrice',
          'costOfGoodsSold',
          'maximumRetailPrice',
      ):
        v1_product[field] = _translate_v2_price_to_v1(val)
      elif field == 'shipping':
        v1_product['shipping'] = _translate_v2_shipping_to_v1(val)
      else:
        v1_product[field] = val

    v1_entry['product'] = v1_product
    v1_payload['entries'].append(v1_entry)

  return v1_payload


def translate_v1_to_v2(
    v1_payload: dict[str, Any], original_v2_payload: dict[str, Any]
) -> dict[str, Any]:
  """Translates Content API (v1) optimized payload back to Merchant API format.

  Args:
    v1_payload: A dictionary representing the optimized v1 payload.
    original_v2_payload: The original v2 payload to reconstruct structure and
      preserve omitted fields.

  Returns:
    A dictionary representing the optimized v2 payload.
  """
  v2_payload = {
      'error-msg': v1_payload.get('error-msg', ''),
      'optimization-results': v1_payload.get('optimization-results', {}),
      'plugin-results': v1_payload.get('plugin-results', {}),
      'optimized-data': {'entries': []},
  }

  v1_entries = v1_payload.get('optimized-data', {}).get('entries', [])
  v2_orig_entries = original_v2_payload.get('entries', [])

  for idx, v1_entry in enumerate(v1_entries):
    v2_orig_entry = v2_orig_entries[idx] if idx < len(v2_orig_entries) else {}

    v2_entry = {}
    for k, v in v1_entry.items():
      if k != 'product':
        v2_entry[k] = v

    v1_product = v1_entry.get('product', {})
    v2_orig_product_input = v2_orig_entry.get('productInput', {})
    v2_product_input = {}

    # Copy top-level metadata fields from v1_product or fallback to original v2
    # values
    for field in ('offerId', 'contentLanguage', 'channel'):
      if field in v1_product:
        v2_product_input[field] = v1_product[field]
      elif field in v2_orig_product_input:
        v2_product_input[field] = v2_orig_product_input[field]

    # Mapping regionalization: targetCountry -> feedLabel
    if 'targetCountry' in v1_product:
      v2_product_input['feedLabel'] = v1_product['targetCountry']
    elif 'feedLabel' in v2_orig_product_input:
      v2_product_input['feedLabel'] = v2_orig_product_input['feedLabel']

    # Determine whether the original document used 'productAttributes' or
    # 'attributes'
    out_attributes_key = 'productAttributes'
    if 'attributes' in v2_orig_product_input:
      out_attributes_key = 'attributes'

    v2_attributes = {}
    for field, val in v1_product.items():
      if field in _METADATA_FIELDS:
        continue

      if field == 'gtin':
        if val is not None:
          v2_attributes['gtins'] = [
              g.strip() for g in val.split(',') if g.strip()
          ]
        else:
          v2_attributes['gtins'] = []
      elif field == 'sizes':
        if val and isinstance(val, list):
          v2_attributes['size'] = val[0]
      elif field in (
          'price',
          'salePrice',
          'costOfGoodsSold',
          'maximumRetailPrice',
      ):
        v2_attributes[field] = _translate_v1_price_to_v2(val)
      elif field == 'shipping':
        v2_attributes['shipping'] = _translate_v1_shipping_to_v2(val)
      else:
        v2_attributes[field] = val

    v2_product_input[out_attributes_key] = v2_attributes
    v2_entry['productInput'] = v2_product_input
    v2_payload['optimized-data']['entries'].append(v2_entry)

  return v2_payload
