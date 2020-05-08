from __future__ import absolute_import, division, print_function

import gin
import tensorflow as tf
from absl import logging

K = tf.keras.backend


@gin.configurable(module="kb.callbacks")
class AbslLogger(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        if logs is not None and len(logs) > 0:
            lines = ["Finished epoch {}".format(epoch)]
            keys = sorted(logs)
            max_len = max(len(k) for k in keys)
            for k in keys:
                lines.append("{}: {}".format(k.ljust(max_len + 1), logs[k]))
            logging.info("\n".join(lines))
