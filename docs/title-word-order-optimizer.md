# Shoptimizer API Title Word Order Optimizer Guide

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

## 1. Overview

Title Word Order Optimizer is a Shoptimizer API optimizer that attempts to re-arrange words in the title so that "high-performing" words of the product are shown near the front of the product's title.

This feature matches a Shoptimizer API request batch of products against a list of Google Product Categories (GPCs) and the weighted high-performing keywords for each GPC stored in a config file.

If a match* was found (whether in the title, description, or productTypes, explained in more detail below), then the high-performing word is copied to the front of the product’s title, surrounded in square brackets ([ ]), and one half-width space is added before the original title. If this “copy”/”prepend” operation results in a title that is over the maximum allowed character length (150 characters), then the word is moved instead of copied. If there are multiple high-performing keywords found, they are prepended in order of descending weight (specified in the config).


* “Match” is defined as full-words only, case-sensitive. Also, single-character words are excluded from the matching.


The config files that specify these GPCs and keywords are “title_word_order_config_{lang}.json”

The format of this config file specified as:

{
  "[GPC ID]": [
    {
      "keyword": [string],
      "weight": [number]
  ],
  ...
}

The generation of the data in this config is left up to the user, but generally a data model is required to determine which keywords for which GPCs are "high-performing" in a live setting, and the output exported periodically to the above format.

This optimizer also makes use of a GPC String representation to GPC ID (in number format) mapping for product batch data that has its GPCs in text format as opposed to number ID format. This mapping conversion will be handled automatically by the optimizer itself, so the config file for this should not need to be modified.

The next sections will describe the detailed design and associated caveats to the above logic. They utilize a shared options config file in the following format:

{
  "descriptionIncluded": [true/false],
  "productTypesIncluded": [true/false],
  "optimizationLevel": ["standard/aggressive"]
}


### Match and Move High-Performing Words Not Only in the Product Title, but also Description and ProductTypes attributes

This feature utilizes the "descriptionIncluded" and "productTypesIncluded" flags in the “title_word_order_options.json” config file that enables whether to also check for high-performing words from not only the product title, but also the product description and productTypes array. If the configuration is enabled (i.e. the value is set to "true"), high-performing words found in the corresponding fields will also be moved to the front of the title.

### Configure "aggressivity" of the GPC matching

This feature utilizes the "optimizationLevel" configuration setting in the “title_word_order_options.json” config file that specifies a string (either "standard" or "aggressive") that determines the level of aggressiveness when doing GPC matching.

These levels are explained as follows:

“standard” - Any product GPCs that are 4 levels deep or more skip optimizing the product for title word order.
“aggressive” - The GPCs are matched as-is (any depth).

### Do not move or copy matching high-performing keywords if they are in a configured list of words to block

Sometimes, even if a word was automatically determined to be high-performing, you may want to still prevent it from being part of the optimization for any other reason.

This feature makes use of an additional config file, "title_word_order_blocklist_{lang}.json", in the format:

[
  "[string]",
  ...
]

Any high-performing words that were found in the product but also were found in this configuration file’s block list do not get prepended to the title. The matching is case-insensitive.

### Do not add high-performing keywords to the front of the title if they are already found near the front of the title (12 first characters for Japanese, 25 first characters for English.

In order to prevent product titles containing duplicates of high-performing words after the optimizer modifies the title, this feature will ensure that words are not moved to the front if they are considered to be already near the front.

"Near the front of the title” is defined as: within a specified language-dependent threshold number of characters, if a full high-performing keyword is contained within that range of characters, it is skipped from being copied to the front of the title. However, if the high-performing keyword is partially within the threshold, or not within the threshold at all, it is copied to the front of the title.

### Do not add high-performing words to the front of the title that are also considered promotional text.

Due to certain words that are considered promotional text having a risk of disapproval of the product, this feature implements safeguards against moving those types of words, with the prerequisite that the promo text optimizer is properly configured by the user.

This feature leverages the promo text optimizer’s configuration to determine if a matching high-performing word is also a promotional text word. If it is, the word is skipped from being added to the front of the title.

### Force title-word-order-optimizer to run after all other optimizers

To avoid conflicting with other optimizers that modify product attributes, this feature ensures that this optimizer runs last, no matter what order it is specified in the query string parameters. This is unique to the title-word-order-optimizer.

