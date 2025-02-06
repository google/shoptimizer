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

"""Caches dynamically loaded optimizers."""
import importlib
import inspect
import pkgutil
import sys

from optimizers_abstract import base_optimizer


class OptimizerCache(object):
  """Caches dynamically loaded optimizers.

  On the first call to the optimizer_classes property, optimizer classes
  will be dynamically loaded from the package specified in the _package_name
  attribute and cached in the _optimizer_classes attribute. Subsequent calls
  to the optimizer_classes property will use the cached optimizer classes
  instead of loading them every time.

  This means the container can have a fast startup time, a slightly delayed
  first request, and fast subsequent requests.

  Typical usage example:

  builtin_optimizer_cache = optimizer_cache.OptimizerCache('optimizers_builtin')
  for optimizer_class in optimizer_cache.optimizer_classes:
    ...do something with the optimizer...

  Attributes:
    _package_name = The package to load optimizers from.
    _optimizer_classes = The cached optimizer classes loaded from the package.
  """

  def __init__(self, package_name: str):
    """Inits OptimizerCache with the specified package name."""
    self._package_name = package_name
    self._optimizer_classes = None

  @property
  def optimizer_classes(self):
    """Returns the optimizer classes stored in this cache.

    The first time this property is called, optimizers will be loaded
    from the package specified in the _package_name attribute.
    """
    if not self._optimizer_classes:
      self._optimizer_classes = self._get_optimizer_classes_in_package()
    return self._optimizer_classes

  def _get_optimizer_classes_in_package(
      self,
  ) -> list[type[base_optimizer.BaseOptimizer]]:
    """Gets optimizer classes in a given package.

    Dynamically loads classes in a package. Classes are loaded dynamically
    so that users can add their own optimizer plugins without having to change
    any Shoptimizer API code. It also means that builtin optimizers and user
    optimizers are loaded in the same way, simplifying the API code structure.

    Returns:
      Optimizer classes which are a subclass of base_optimizer.BaseOptimizer.
    """
    sys.path.append(self._package_name)
    class_info_list = []
    # Imports all modules from a given package and adds classes to
    # class_info_list
    for module_info in pkgutil.iter_modules([self._package_name]):
      module = importlib.import_module(
          module_info.name, package=self._package_name)
      class_info_list.extend(inspect.getmembers(module, inspect.isclass))

    # Creates a list of base_optimizer classes
    optimizer_classes = [
        class_type for _, class_type in class_info_list
        if issubclass(class_type, base_optimizer.BaseOptimizer)
    ]
    return optimizer_classes
