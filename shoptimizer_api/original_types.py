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

"""Original type aliases."""

# OrderedDict is deprecated and reimplemented between major
# versions of Python 3.6 and 3.9. It also moves from `typing`
# to `collections`. This makes typing it correctly difficult
# between Python versions
#
# To solve for this, we use forward-reference annotations per:
# * https://www.python.org/dev/peps/pep-0484/#forward-references
# * https://stackoverflow.com/a/52626233
MinedAttributes = dict[str, 'OrderedDict[str, Any]']
