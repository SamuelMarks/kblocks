from __future__ import absolute_import, division, print_function

from typing import Callable

import tensorflow as tf


class SideEffect(tf.keras.layers.Layer):
    def __init__(self, fn: Callable, **kwargs):
        self._fn = fn
        super(SideEffect, self).__init__(**kwargs)

    def call(self, inputs):
        deps = self._fn(inputs)
        with tf.control_dependencies(tf.nest.flatten(deps)):
            return tf.nest.map_structure(tf.identity, inputs)
