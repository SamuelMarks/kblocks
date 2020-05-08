from __future__ import absolute_import, division, print_function

from typing import Callable

import tensorflow as tf

from kblocks.tf_typing import (
    NestedTensorLike,
    NestedTensorSpec,
    TensorLike,
    TensorLikeSpec,
)


def to_input(spec: TensorLikeSpec) -> TensorLike:
    if isinstance(spec, tf.TensorSpec):
        return tf.keras.Input(
            shape=spec.shape[1:], batch_size=spec.shape[0], dtype=spec.dtype
        )
    elif isinstance(spec, tf.RaggedTensorSpec):
        return tf.keras.Input(
            shape=spec._shape[1:],
            batch_size=spec._shape[0],
            dtype=spec._dtype,
            ragged=True,
        )
    elif isinstance(spec, tf.SparseTensorSpec):
        return tf.keras.Input(
            shape=spec.shape[1:],
            batch_size=spec.shape[0],
            dtype=spec.dtype,
            sparse=True,
        )
    else:
        raise TypeError("Unrecognized spec type {}".format(type(spec)))


def to_spec(tensor: TensorLike) -> TensorLikeSpec:
    """Convert a (Ragged/Sparse)Tensor to the corresponding TensorSpec."""
    if isinstance(tensor, tf.RaggedTensor):
        return tf.RaggedTensorSpec.from_value(tensor)
    elif isinstance(tensor, tf.Tensor):
        return tf.TensorSpec.from_tensor(tensor)
    elif isinstance(tensor, tf.SparseTensor):
        return tf.SparseTensorSpec.from_value(tensor)
    else:
        raise TypeError("Expected TensorLikeSpec, got {}".format(tensor))


def map_spec(
    map_fn: Callable[[NestedTensorLike], NestedTensorLike], spec: NestedTensorSpec
) -> NestedTensorSpec:
    """
    Get the specification corresponding to a spec transformation.

    Args:
        map_fn: function applied.
        spec: possibly nested input spec structure.

    Returns:
        possibly nested output spec structure corresponding to the spec of
        map_fn applied to tensors corresponding to input spec.
    """

    def gen():
        raise NotImplementedError()

    dataset = tf.data.Dataset.from_generator(
        gen,
        tf.nest.map_structure(lambda spec: spec.dtype),
        tf.nest.map_structure(lambda spec: spec.shape),
    )
    dataset = dataset.map(map_fn)
    return dataset.spec


def shape(spec: TensorLikeSpec) -> tf.TensorShape:
    if isinstance(spec, tf.RaggedTensor):
        return spec._shape
    else:
        return spec.shape


def dtype(spec: TensorLikeSpec) -> tf.DType:
    if isinstance(spec, tf.RaggedTensor):
        return spec._dtype
    else:
        return spec.dtype
