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

"""Utilities related to image processing and scoring."""
import logging
import os
import pathlib

# Need to set the log level before importing tensorflow to disable info/debug.
# Can upgrade to TF 2.5 to remove this.
# https://github.com/tensorflow/tensorflow/issues/31870
#

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow.compat.v1 as tf


#  The MODEL_LOCATION must contain a `saved_model.pb` file containing a
#  trained Tensorflow model (see https://www.tensorflow.org/guide/saved_model).
#  The model should be a trained single-label classification model where the
#  the first output contains a score of 0.0 if the image is high quality and
#  a score of 1.0 if the image is low quality.
#
#  See https://cloud.google.com/vision/automl/docs/edge-quickstart for details
#  on how to train your own model using AutoML Vision.
MODEL_LOCATION = os.path.join(
    pathlib.Path(__file__).parent.resolve(), 'resources', 'image_util')

DEFAULT_SCORE: float = float('inf')


def score_image(image_data: bytes) -> float:
  """Scores the provided image with a trained Tensorflow model.

  Returns float('inf') if the image cannot be scored to represent
  the worst possible score.

  Args:
    image_data: Image binary data to score.

  Returns:
    Score from 0 (best quality) to 1 (lowest quality) image, according to
    the model. Returns float('inf') if the image cannot be scored.
  """
  if not image_data:
    return DEFAULT_SCORE

  if not _saved_model_exists():
    logging.warning('Could not find model in `%s`. Cannot score image.',
                    MODEL_LOCATION)
    return DEFAULT_SCORE

  with tf.Session(graph=tf.Graph()) as session:
    try:
      tf.saved_model.loader.load(session, ['serve'], MODEL_LOCATION)
      score = session.run('scores:0', feed_dict={'Placeholder:0': [image_data]})
    except tf.errors.OpError as e:
      logging.debug('Error when scoring image: %s', repr(e))
      return DEFAULT_SCORE

    return score[0][0]


def _saved_model_exists() -> bool:
  """Identifies if a saved_model.pb file exists in the expected MODEL_LOCATION.

  Returns:
    True if the mode file can be found, False otherwise.
  """
  return os.path.isfile(os.path.join(MODEL_LOCATION, 'saved_model.pb'))
