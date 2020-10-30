# Shoptimizer API Developer Guide

_Copyright 2019 Google LLC. This solution, including any related sample code or
data, is made available on an “as is,” “as available,” and “with all faults”
basis, solely for illustrative purposes, and without warranty or representation
of any kind. This solution is experimental, unsupported and provided solely for
your convenience. Your use of it is subject to your agreements with Google, as
applicable, and may constitute a beta feature as defined under those agreements.
To the extent that you make any data available to Google in connection with your
use of the solution, you represent and warrant that you have all necessary and
appropriate rights, consents and permissions to permit Google to use and process
that data. By using any portion of this solution, you acknowledge, assume and
accept all risks, known and unknown, associated with its usage, including with
respect to your deployment of any portion of this solution in your systems, or
usage in connection with your business, if at all._

[TOC]

## 0. About

This document explains how to integrate the Shoptimizer API (referred to as
'Shoptimizer') with your existing Content API for Shopping solution. It also
describes the technical architecture, how to create or custom optimizations, and
how to track optimization performance.

For an explanation of how to pull the source code and run Shoptimizer, see the
[install guide](./install-guide.md).

## 1. Prerequisites

*   The Shoptimizer source code (see the [install guide](./install-guide.md))
*   A Python 4.8+ environment

## 2. Architecture Overview

### 2.1 Shoptimizer Workflow

![Shoptimizer Workflow](./img/shoptimizer-workflow.jpg)

### 2.2 API Specification

Shoptimizer consists of a single endpoint called `optimize`, which is documented
below.

--------------------------------------------------------------------------------

__optimize__

**URL**

`/batch/optimize`

**Method**

`POST`

**URL Query Params**

_**Required:**_

*   (None)

_**Optional:**_

*   `lang=[en/ja]`
*   `adult-optimizer=(true/false)`
*   `color-length-optimizer=(true/false)`
*   `condition-optimizer=(true/false)`
*   `description-optimizer=(true/false)`
*   `gtin-optimizer=(true/false)`
*   `identifier-exists-optimizer=(true/false)`
*   `invalid-chars-optimizer=(true/false)`
*   `mpn-optimizer=(true/false)`
*   `product-type-length-optimizer=(true/false)`
*   `size-length-optimizer=(true/false)`
*   `title-length-optimizer=(true/false)`
*   `title-optimizer=(true/false)`

"lang" will control which language is used for certain optimizers that require
language-specific token parsing. The supported language values are: "en"
(English), "ja" (Japanese). If the "lang" parameter is not supplied, it will
default to Japanese. This directly maps to which language-specific config file
is used under the config/ directory. These files can be edited by the user as
needed.

Apart from "lang", setting any of the other parameters to true will run the
associated optimizer. If any of these parameters are not provided in the
request, they will default to false. See section 4. 'Available Optimizers' for
descriptions of the available optimizers.

**Request Body**

The request body should contain a JSON payload of product data in the same
format as a Content API for Shopping
[products.custombatch](https://developers.google.com/shopping-content/reference/rest/v2.1/products/custombatch)
call.

**Success Response**

*   **Code:** 200 <br />
    **Content:**
    `json
    {
        "optimization-results": {
            "optimizer-name": {
                "error_msg": "",
                "num_of_products_optimized": 0,
                "result": "{success/failure}"
            },
        },
        "optimized-data": {
            ...optimized product batch data...
        },
        "plugin-results": {
            "plugin-name": {
                "error_msg": "",
                "num_of_products_optimized": 0,
                "result": "{success/failure}"
            }
        }
    }`

**Error Response**

*   **Code:** 404 NOT FOUND <br />
    **Content:**
    `json
    {
      "error": "URL not found"
    }`

    OR

*   **Code:** 400 BAD REQUEST <br />
    **Content:**
    `json
    {
      "error-msg": "Error msg.",
      "optimization-results": {},
      "optimized-data": {},
      "plugin-results": {}
    }`

--------------------------------------------------------------------------------

### 2.3 Example Usage

The following file can be imported into [Postman](https://www.postman.com/) to
create a suite of example HTTP requests:

`/shoptimizer/shoptimizer_api/postman/shoptimizer_integration_tests.postman_collection.json`

Within the Postman suite, the `{{baseApiUrl}}` environment variable can be set
to a local host or remote host, such as a Google Cloud Run URL.

Postman can also be used to
[generate code snippets](https://learning.postman.com/docs/postman/sending-api-requests/generate-code-snippets/)
for use within your Content API Client.

## 3. Config Files

***Warning: If the below config files are changed to not follow the specified
structure or key names, the corresponding optimizers may stop functioning.***

In order for some of the optimizations (shown below) to have any effect,
configuration files located in shoptimizer_api/config must be correctly set to
your specific business requirements. With the exception of the
"brand_blocklist.json" config file, the filename of each config must be suffixed
with "\_{lang}", where {lang} is the ISO 639-2 language code that your request's
"lang" parameter specifies. Each config file is explained in the table below.

Config File Name                       | Used by Optimizer(s)                   | How to Configure
-------------------------------------- | -------------------------------------- | ----------------
adult_optimizer_config_{lang}.json     | adult-optimizer                        | Set the \"**adult_product_types**\" section to a list of strings representing adult-oriented [Product Types](https://support.google.com/merchants/answer/6324406?hl=en). Do not use the fully qualified path of the entire Product Types string, but instead only put individual types into each entry in this config section (e.g. only look for "Dresses", not "Home > Women > Dresses > Maxi Dresses"). Set the \"**adult_google_product_categories**\" section to a list of key-value pairs, the key being any full [Google Product Category](https://support.google.com/merchants/answer/6324436?hl=en) (the optimizer can match any sub-category of an upper-tier), and the value a list of strings representing tokens that will indicate the product is adult-oriented. Setting the value to a single-element list with the token "\*" will flag the entire GPC as adult-oriented. The optimizer will then check if the product is either of an adult-oriented Product Type, OR an adult-oriented GPC that contains adult-oriented tokens to set the adult attribute. See the default configs for examples.
brand_blocklist.json                   | title-optimizer, description-optimizer | Add a list of strings representing brands that should not be appended to the title or description of the product. See the default configs for examples.
color_optimizer_config_{lang}.json     | title_optimizer, description-optimizer | Set \"**color_terms**\" to a dictionary of key-value pairs representing colors to be mined and map complex colors to simple colors. Complex colors get appended to title/description, and simple colors get added to the color field. See the default configs for examples.
condition_optimizer_config_{lang}.json | condition-optimizer | Set the \"**used_tokens**\" section to a list of string representing tokens in a product's title or description that indicate if a product should be set to "Used". Set the \"**excluded_product_categories**\" section to a list of strings representing any full [Google Product Category](https://support.google.com/merchants/answer/6324436?hl=en) (the optimizer can match any sub-category of an upper-tier) that should exclude this optimizer from checking for tokens in the used_tokens section. Set the \"**target_product_categories**\" section to a list of key-value pairs, the key being any full [Google Product Category](https://support.google.com/merchants/answer/6324436?hl=en) (the optimizer can match any sub-category of an upper-tier), and the value a list of strings representing tokens that will indicate the product is Used. This is useful for category-specific tokens. See the default configs for examples.
gender_optimizer_config_{lang}.json    | title_optimizer, description-optimizer | Set the \"**adult_product_categories**\" section to a list of strings representing partial [Google Product Categories](https://support.google.com/merchants/answer/6324436?hl=en) (any part of a tier can match a product's category) that indicate products in those categories should be mined for adult genders. Similarly, set the \"**baby_product_categories**\" to a list of partial GPCs that indicate products in those categories should be mined for baby genders. The next three sections, "female", "male", and "unisex" specify the terms to search the [Product Type](https://support.google.com/merchants/answer/6324406?hl=en) field and description for, and the \"**\*__replacement**\" fields specify the desired terms to set as the gender in the title (for either "baby" or "adult" types of products). See the default configs for examples.

## 4. Integrating Shoptimizer with your Content API Client

This section explains how to call Shoptimizer from your Content API Client. It
assumes you already have Shoptimizer running on your chosen infrastructure. If
you do not have Shoptimizer running yet, see the
[install guide](./install-guide.md).

The code samples in this section are written in Python, but any language which
is capable of sending HTTP requests can call Shoptimizer. The code samples do
not contain error handling for the sake of clarity, but production code should
also handle error conditions, such as network issues.

### 4.1 Authentication

Make sure you are authenticated with the Docker host where the Shoptimizer
container is running. Authentication will depend on the platform you are using
to host the Shoptimizer container. See the documentation for your chosen Docker
host for details on how to authenticate.

If you are running Shoptimizer with Google Cloud Run, you can get a JWT for
authentication, shown below.

__Example Code to Get a Cloud Run JWT__

```python
# Replace [SHOPTIMIZER-BASE-URL] with your Shoptimizer base URL
token_request_url = f'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience=[SHOPTIMIZER--BASE-URL]'
token_request_headers = {'Metadata-Flavor': 'Google'}

# Fetches the token
response = requests.get(token_request_url, headers=token_request_headers)
jwt = response.content.decode('utf-8')
```

### 4.2 Calling Shoptimizer

The Shoptimizer endpoint is constructed as follows:

[POST]`{HOST}:{PORT}/shoptimizer/v1/batch/optimize?{OPTIMIZATION-QUERY-STRING}`

The body should contain a batch of product data encoded as JSON, in the same
format as
[products.custombatch](https://developers.google.com/shopping-content/reference/rest/v2.1/products/custombatch).

`OPTIMIZATION-QUERY-STRING` is a list of query parameters in the format
`{optimizer-key}={true/false}` that determines which optimizers Shoptimizer will
run. If you exclude an optimizer completely from the query string, it will not
be run.

See section 4. 'Available Optimizers' for a list of available default optimizer
keys.

Consider creating a config file for your Content API client so that you can
easily toggle optimizers on and off.

__Example Endpoint__

`http://0.0.0.0:8080/shoptimizer/v1/batch/optimize?mpn-optimizer=true&title-length-optimizer=true`

__Example Code to Call Shoptimizer__

```python
# Converts a batch of product data from a Python dictionary to a JSON string
product_batch_json = json.dumps(original_product_batch_dictionary)

# Sets up a dictionary to specify which optimizers to run
optimizers_to_run = {
  'mpn-optimizer': 'true'
  'title-length-optimizer': 'true'
  }

# Makes the call to Shoptimizer
headers = {
          'Authorization': f'bearer {jwt}',
          'Content-Type': 'application/json'
        }

response = requests.request(
      'POST',
      '[SHOPTIMIZER-BASE-URL]/shoptimizer/v1/batch/optimize', # Replace [SHOPTIMIZER-BASE-URL] with your Shoptimizer base URL
      data=product_batch_json,
      headers=headers,
      params=optimizers_to_run)
```

### 4.3 Parsing the Response

A successful call to Shoptimizer will return a `200` HTTP status code and JSON
in the following format:

```json
{
    "optimization-results": {
        "optimizer-name": {
            "error_msg": "",
            "num_of_products_optimized": 0,
            "result": "{success/failure}"
        },
    },
    "optimized-data": {
        ...optimized product batch...
    },
    "plugin-results": {
        "plugin-name": {
            "error_msg": "",
            "num_of_products_optimized": 0,
            "result": "{success/failure}"
        }
    }
}

```

The JSON contains three parts:

*   __optimized-data__: The optimized product batch. This can be sent to Content
    API for Shopping.

*   __optimization-results__: A list of the results for each built-in optimizer
    in the format `optimizer-name: {result-dictionary}`. This can be read to
    track the performance and detect errors that occurred within each optimizer.
    The resulting dictionary for each optimizer is in the following format:

    *   _error_msg_: Empty if no error occurred while running the optimizer,
        otherwise an error message.
    *   _num_of_products_optimized_: The number of products that were affected
        by this optimizer.
    *   _result_: `success` if the optimizer finished running without errors, or
        `failure` otherwise.

*   __plugin-results__: A list of the results for each plugin optimizer in the
    format `plugin-name: {result-dictionary}`. This can be read to track the
    performance and detect errors that occurred within plugins. The result
    dictionary for each plugin is in the following format:

    *   _error_msg_: Empty if no error occurred while running the plugin,
        otherwise an error message.
    *   _num_of_products_optimized_: The number of products that were affected
        by this plugin.
    *   _result_: `success` if the plugin finished running without errors,
        otherwise `failure`.

To get the optimized product batch, parse out `optimized-data` from the
response.

__Example Code to Parse Shoptimizer Response__

```python
# Parses the JSON response data
shoptimizer_response_dict = json.loads(response.text)

# Parses out the optimized product batch
optimized_product_batch = shoptimizer_response_dict.get('optimized-data')
```

### 4.4 Checking for Errors

#### 4.4.1 Bad Requests

If Shoptimizer receives a bad request, it will return a `400` HTTP response code
and JSON in the following format:

```json
{
    "error-msg": "Descriptive error message.",
    "optimization-results": {},
    "optimized-data": {},
    "plugin-results": {}
}

```

__Example Code to Check for Errors__

```python
# Checks for top level errors in the Shoptimizer API response, and returns the original product batch if any encountered
if shoptimizer_response_dict.get('error-msg', ''):
  logging.error('Encountered an error in the Shoptimizer API response', response_dict['error-msg'])
  return original_product_batch_dictionary
```

#### 4.4.2 Optimizer Errors

Each optimizer runs within an isolation block that will prevent the Shoptimizer
container from crashing if an unexpected error is encountered. This means that
an individual optimizer may encounter an error, but Shoptimizer can still return
a successful response since other optimizers ran without errors. If an optimizer
encounters an unexpected error, it will return an unmodified product batch, so
there is no need to worry about unexpected optimizer errors causing data
corruption.

To check if an optimizer encountered an unexpected error, parse the
`optimization-results` and `plugin-results` from the Shoptimizer API response.

__Example Code to Check Optimizer Results__

```python
# Checks for any errors that occurred within individual optimizers.
optimization_results = response_dict.get('optimization-results', '')

for optimizer_name, optimizer_results in optimization_results.items():
      if optimizer_results.get('result', '') == 'failure':
        logging.error('optimizer %s enountered an error: %s', optimizer_name,  optimizer_results.get('error_msg'))

```

### 4.5 Complete Code Sample

```python
def shoptimize(original_product_batch_dictionary: Dict[str, Any]) -> Dict[str, Any]:
  """Optimizes a batch of product data by sending it to the Shoptimizer (optimization) API.

  Args:
    original_product_batch_dictionary: The batch of product data to be optimized.

  Returns:
    The optimized batch of product data if no errors encountered,
    or the original batch of product data otherwise.
  """

  # Converts a batch of product data from a Python dictionary to a JSON string
  product_batch_json = json.dumps(original_product_batch_dictionary)

  # Sets up a dictionary to specify which optimizers to run
  optimizers_to_run = {
    'mpn-optimizer': 'true'
    'title-length-optimizer': 'true'
    }

  # Makes the call to Shoptimizer
  headers = {
            'Authorization': f'bearer {jwt}',
            'Content-Type': 'application/json'
          }

  response = requests.request(
        'POST',
        '[SHOPTIMIZER-URL]/shoptimizer/v1/batch/optimize', # Replace [SHOPTIMIZER-URL] with your Shoptimizer URL
        data=product_batch_json,
        headers=headers,
        params=optimizers_to_run)

  # Parses the JSON response data
  shoptimizer_response_dict = json.loads(response.text)

  # Checks for top level errors in the Shoptimizer API response, and returns the original product batch if any encountered
  if shoptimizer_response_dict.get('error-msg', ''):
    logging.error('Encountered an error in the Shoptimizer API response', response_dict['error-msg'])
    return original_product_batch_dictionary

  # Checks for any errors that occurred within individual optimizers.
  optimization_results = response_dict.get('optimization-results', '')

  for optimizer_name, optimizer_results in optimization_results.items():
        if optimizer_results.get('result', '') == 'failure':
          logging.error('optimizer %s enountered an error: %s', optimizer_name,  optimizer_results.get('error_msg'))

  # Parses out the optimized product batch and returns it
  return shoptimizer_response_dict.get('optimized-data')
```

## 5. Activating Optimizers

Append `optimizer-key=true` as a URL parameter in your call to Shoptimizer for
each optimizer you want to run.

For example, to run the mpn-optimizer and gtin-optimizer, use the following
endpoint:

`.../shoptimizer/v1/batch/optimize?mpn-optimizer=true&gtin-optimizer=true`

## 6. Writing a Plugin

If you want to add your own sanitzation and optimization code to Shoptimizer,
you can write a plugin to do this.

To create a plugin, open the Shoptimizer solution and follow the steps below.

_Note: See `shoptimizer_api/optimizers_plugins/my_plugin.py` for an example
plugin. You can copy this plugin and then update the `optimize` method to
contain your own specific logic._

### 6.1 Create a New Module

In the `shoptimizer_api/optimizers_plugins` directory, create a new Python
module.

There is no required naming convention for plugin optimizers, but it is
recommended to use the format `{optimization-description}_plugin.py`.

### 6.2 Implement from BaseOptimizer

Your plugin should inherit from `base_optimizer.BaseOptimizer`.

This requires implementing:

*   __`_OTPIMIZER_PARAMETER`__: A class attribute that can be used to enable or
    disable your plugin.
*   __`optimize(self, data: Dict[str, Any]) -> int`__: The entrypoint for
    optimization logic. This method takes in a batch of product data and returns
    the number of products affected by the optimizer.

Since your plugin will be dynamically loaded into Shoptimizer, you do not need
to (and should not) change any of the Shoptimizer code outside of your plugin.

__Sample Plugin__

```python
from typing import Any, Dict

from optimizers_abstract import base_optimizer


class MyPlugin(base_optimizer.BaseOptimizer):
  """An example plugin."""

  _OPTIMIZER_PARAMETER = 'my-plugin'

  def optimize(self, data: Dict[str, Any]) -> int:
    """The entrypoint for optimization logic.

    Args:
      data:  A dictionary containing product data.

    Returns:
      The number of products affected by this optimization: int
    """
    num_of_products_optimized = 0

    for entry in data['entries']:
      product = entry['product'] # Grabs the product
      product['title'] = 'Optimized Title' # Sets the title to some optimized value
      num_of_products_optimized = num_of_products_optimized + 1 # Increments the number of products optimized
      base_optimizer.set_optimization_tracking(entry, base_optimizer.OPTIMIZED) # Sets optimization tracking

    return num_of_products_optimized

```

### 6.3 Install MeCab

Shoptimizer uses MeCab, a natural language processing tool that tokenizes
Japanese text. Install it before running unit tests. If you do not want to run
the unit tests, you do not have to install MaCab

OSX:

```
brew install mecab mecab-ipadic git curl xz
git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
echo yes | mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -a
```

Linux:

```
apt-get update
apt-get -y install mecab libmecab-dev mecab-ipadic-utf8 git make curl xz-utils file sudo
git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
echo yes | mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -a
```

### 6.4 Run Unit Tests

Run Python unit test module to test optimizers. For example, when you test
title_optimizer, run the command below:

```
python -m unittest optimizers_builtin.title_optimizer_test
```

### 6.5 Update Shoptimizer

After creating your plugin, follow the [install guide](./install-guide.md) to
redeploy the updated Shoptimizer.

You can call your new Plugin from your Content API Client by appending the
`{_OPTIMIZER_PARAMETER}=true` value to the end of the query string. For example,
to call the sample plugin above:

`{HOST}:{PORT}/shoptimizer/v1/batch/optimize?my-plugin=true`

## 7. Tracking Optimization Performance

There are two ways to track the performance of optimized products:

1.  Log the Shoptimizer response
2.  View customLabels in Google Ads

### 7.1 Log the Shoptimizer Response

The Shoptimizer response contains a list of results for each optimizer. Each
optimizer result contains a field `num_of_products_optimized` that contains a
count of the number of products that were affected. Log or store this result on
your infrastructure to keep track of how effective specific optimizers are.

Section 4.3 'Parsing the Response' details the format of the Shoptimizer
response.

### 7.2 View customLabel Fields in Google Ads

If you configured the `PRODUCT_TRACKING_FIELD` environment variable, optimized
products will have one of 3 values set in their customLabel field:

-   __SANITIZED__: Invalid data was removed or corrected. If this had not been
    done the product would have been disapproved.
-   __OPTIMIZED__: Data was modified in an attempt to improve performance, but
    the original data was not incorrect.
-   __SANITIZED_AND_OPTIMIZED__: The product was both sanitized and optimized.

You can filter by these values in Google Ads to view data about the performance
of the optimized products.

See section 4.3 'Run the Container' in the [install guide](./install-guide.md)
for details on configuring the environment variables.

## 8. Run Unit Tests

You can run all of the unit tests in the solution by running `test_runner.py`.
