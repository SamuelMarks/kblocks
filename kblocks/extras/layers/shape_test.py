from typing import Tuple

import numpy as np
import tensorflow as tf

from kblocks.extras.layers import shape as shape_layers


def inp(shape):
    return tf.keras.layers.Input(shape=shape[1:], batch_size=shape[0])


class ShapeTest(tf.test.TestCase):
    def assertTensorShapeEquals(self, x: tf.Tensor, expected: Tuple[int, ...]):
        return self.assertEqual(tuple(x.shape), expected)

    def test_flatten_leading_dims(self):
        x = inp((2, 3, 4))
        self.assertTensorShapeEquals(shape_layers.flatten_leading_dims(x, 1), (2, 3, 4))
        self.assertTensorShapeEquals(shape_layers.flatten_leading_dims(x, 2), (6, 4))
        self.assertTensorShapeEquals(shape_layers.flatten_leading_dims(x, 3), (24,))
        with self.assertRaises(ValueError) as context:
            shape_layers.flatten_leading_dims(x, 2, 8)
        self.assertTrue("Cannot reshape a tensor with" in str(context.exception))

        x = inp((None, None, 4))
        self.assertTensorShapeEquals(
            shape_layers.flatten_leading_dims(x, 1), (None, None, 4)
        )
        self.assertTensorShapeEquals(shape_layers.flatten_leading_dims(x, 2), (None, 4))
        self.assertTensorShapeEquals(shape_layers.flatten_leading_dims(x, 3), (None,))

        x = tf.RaggedTensor.from_row_lengths([2, 3, 4], [2, 1])
        self.assertTensorShapeEquals(shape_layers.flatten_leading_dims(x, 2), (3,))

    def test_reshape_leading_dim(self):
        x = inp((10, 3))
        self.assertTensorShapeEquals(
            shape_layers.reshape_leading_dim(x, (2, 5)), (2, 5, 3)
        )
        self.assertTensorShapeEquals(
            shape_layers.reshape_leading_dim(x, (5, -1)), (5, 2, 3)
        )

        x = inp((None, 3))
        self.assertTensorShapeEquals(
            shape_layers.reshape_leading_dim(x, (-1, 2)), (None, 2, 3)
        )
        self.assertTensorShapeEquals(
            shape_layers.reshape_leading_dim(x, (5, 2)), (5, 2, 3)
        )

    def test_reshape_ragged_leading_dim(self):
        x = tf.zeros((100,), dtype=tf.float32)
        rl = tf.constant([50, 30, 10, 10])
        rt = tf.RaggedTensor.from_row_lengths(x, rl)
        out = shape_layers.reshape_leading_dim(rt, (2, 2))

        self.assertEqual(out.ragged_rank, 2)
        np.testing.assert_equal(self.evaluate(out.row_splits), [0, 2, 4])
        np.testing.assert_equal(
            self.evaluate(out.values.row_splits), [0, 50, 80, 90, 100]
        )

    def test_as_batched(self):
        x = inp((10, 3))
        self.assertTensorShapeEquals(shape_layers.as_batched(x, 5), (5, 2, 3))
        self.assertTensorShapeEquals(shape_layers.as_batched(x, 5, 2), (5, 2, 3))
        self.assertTensorShapeEquals(
            shape_layers.as_batched(x, element_size=2), (5, 2, 3)
        )

    def test_as_batched_tensors(self):
        ld = 10
        x = inp((ld, 3))
        self.assertTensorShapeEquals(shape_layers.as_batched(x, ld // 2), (5, 2, 3))
        self.assertTensorShapeEquals(shape_layers.as_batched(x, ld // 2, 2), (5, 2, 3))
        self.assertTensorShapeEquals(shape_layers.as_batched(x, 5, ld // 5), (5, 2, 3))


if __name__ == "__main__":
    tf.test.main()
    # x = inp((None, None, 4))
    # shape_layers.flatten_leading_dims(x, 1).shape, (None, None, 4)
