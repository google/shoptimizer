# Shoptimizer

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

## Overview

Shoptimizer is a REST API for automating improvements to product data for Google
Shopping.

Shoptimizer accepts a JSON payload of product data in the same format as a
Content API for Shopping
[products.custombatch](https://developers.google.com/shopping-content/reference/rest/v2.1/products/custombatch)
call. Shoptimizer sanitizes and optimizes the product data, and returns it to
the client. This optimized product data can then be sent to Content API for
Shopping.

Please refer to the following documentation for how to use this solution.

1.  [Installation Guide](./docs/install-guide.md)
2.  [Developer Guide](./docs/developer-guide.md)

### Glossary of Terms

Term                                                                        | Definition
--------------------------------------------------------------------------- | ----------
[Merchant Center](https://www.google.com/retail/solutions/merchant-center/) | A tool that lets you upload and store product data to Google and make it available for Shopping ads.
[Content API for Shopping](https://developers.google.com/shopping-content)  | An API for interacting with Merchant Center.
Content API Client                                                          | A solution for sending product data to Content API for Shopping. This is a generic term and does not refer to a specific codebase. For example, this could be a Python program that uses Google APIs to make Content API for Shopping calls to upload data to Merchant Center.
Shoptimizer                                                                 | A REST API that can be integrated into a Content API Client to automate improvements to product data before it is sent to Merchant Center.
Optimizer                                                                   | An isolated block of optimization logic within Shoptimizer. Individual optimizers can be enabled and disabled.
Builtin Optimizer                                                           | An optimizer that comes bundled with Shoptimizer.
Plugin Optimizer                                                            | A custom optimizer that you can develop and add to Shoptimzier.
Optimization                                                                | Modifying data in an attempt to improve performance. The original data is not incorrect.
Sanitization                                                                | Correcting or removing invalid data. If this data is not corrected or removed, the product will be disapproved.

## Optimizer Explanations

Shoptimizer contains the following built-in optimizers. Note: some of these
optimizer modules rely on configuration files to execute their business logic.
Please see the section on
[Config Files](./docs/developer-guide.md#3_Config-Files) to understand how to
configure these properly.

Optimizer Key                 | Type                        | Description
----------------------------- | --------------------------- | -----------
adult-optimizer               | _Optimization_              | Sets the "adult" attribute on a product when the optimizer determines that the product is adult-oriented.
color-length-optimizer        | _Optimization_              | Fixes the length of the color attribute. This module does three things: 1. Ensures the total length of the color attribute is <= 100 characters 2. Removes any color with a length > 40 characters 3. Ensures there are no more than 3 colors in the list of colors. This will prevent the color attribute from being rejected.
condition-optimizer           | _Sanitization_              | If the condition field is specified as "new", but other fields in the product imply that the condition is otherwise, this optimizer will set the condition value to "used". This will lead to the product avoiding disapproval. (It is also possible that accounts that misrepresent condition can be suspended.)
description-optimizer         | _Optimization_              | Appends the following product attributes to the product description if they could be mined: brand, color, sizes, gender. It will also create the description from these attributes if it does not exist. These mined fields being in the description have a possibility to increase ad performance. (This optimizer will also perform attribute mining: brand, color, sizes, and gender attributes will be added to the product fields if they do not exist and could be mined.)
gtin-optimizer                | _Sanitization_              | The last digit of the gtin must match the formula defined [here](https://www.gs1.org/services/how-calculate-check-digit-manually). If the gtin fails this check, this optimizer will delete the gtin field from the product. This will lead to the product avoiding disapproval.
identifier-exists-optimizer   | _Sanitization_              | Removes invalid identifierExists fields. Items that have a brand, mpn, or gtin set and identifierExists as "false" cause disapproval, so this optimizer will delete the identifierExists value in these cases, which defaults the value to true via Content API. This will lead to the product avoiding disapproval.
invalid-chars-optimizer       | _Sanitization/Optimization_ | Removes invalid chars from the product title and description. Invalid chars are those with code points that map to the Unicode private use area (0xE000-0xF8FF). This will lead to the product avoiding disapproval if the invalid char is in the title, and lead to the description not being rejected if the invalid char is in the description.
mpn-optimizer                 | _Sanitization_              | Removes invalid MPN fields. Certain MPN values will cause products to be disapproved. If an invalid MPN value is detected, this optimizer will delete it. This will lead to the product avoiding disapproval. The list of invalid MPNs can be found in `mpn_optimizer.py`.
product-type-length-optimizer | _Optimization_              | Fixes the length of the productTypes attribute. This module ensures there are no more than 10 categories in the list of productTypes.
size-length-optimizer         | _Optimization_              | The sizes attribute consists of a list containing a single string. This optimizer will trim the sizes attribute to 100 characters and ensure the sizes attribute only contains one value. This will prevent the sizes attribute from being rejected.
title-length-optimizer        | _Sanitization/Optimization_ | Truncates title to the max title length if its length exceeds the max value. This will lead to the product avoiding disapproval. Also, if the title is a truncated version of the description, and there is space to expand the title, the title will be expanded. This is expected to improve product performance.
title-optimizer               | _Sanitization/Optimization_ | Optimizes title. It will create the title from the description if the title does not exist, truncate the title if it overflows, or complement the title with the description if the title is truncated from the description. It also appends product attributes to the title after mining them. This is expected to improve product performance. Supported attributes: gender, color, sizes, brand. (This optimizer will also perform attribute mining: brand, color, sizes, and gender attributes will be added to the product fields if they do not exist and could be mined.)
