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
"""Runs all unit tests within the solution."""
import argparse
import os
import sys
import unittest


def main(test_path, test_pattern):
  # Discover and run tests.
  suite = unittest.loader.TestLoader().discover(test_path, test_pattern)
  return unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument(
      '--test-pattern',
      help='The file pattern for test modules, defaults to *_tests.py.',
      default='*_test.py')
  args = parser.parse_args()

  test_paths = [os.getcwd(),
                f'{os.getcwd()}/optimizers_abstract',
                f'{os.getcwd()}/optimizers_builtin',
                f'{os.getcwd()}/optimizers_plugins']
  test_failed = False
  for path in test_paths:
    result = main(path, args.test_pattern)
    if not result.wasSuccessful():
      test_failed = True
  if test_failed:
    sys.exit(1)
