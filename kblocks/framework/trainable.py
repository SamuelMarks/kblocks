from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import logging
import os
import tensorflow as tf
import gin
from typing import Callable

from kblocks.framework.problems import Problem
from kblocks.framework.pipelines import Pipeline
from kblocks import callbacks as cb
from kblocks.tf_typing import NestedTensorLikeSpec
from kblocks.framework.problems.core import Split
from typing import Sequence, Mapping, Any, Optional


@gin.configurable(module='kb.framework')
class Trainable(object):

    def __init__(self, problem: Problem, pipeline_fn: Callable[
        [NestedTensorLikeSpec, NestedTensorLikeSpec], Pipeline],
                 optimizer_fn: Callable[[], tf.keras.optimizers.Optimizer],
                 model_dir: str):
        self._model_dir = os.path.expanduser(os.path.expandvars(model_dir))
        self._problem = problem
        with problem:
            self._pipeline = pipeline_fn(problem.features_spec,
                                         problem.outputs_spec)
            optimizer = optimizer_fn()
            if self._pipeline.model is not None:
                self._pipeline.model.compile(
                    loss=self._problem.loss,
                    metrics=self._problem.metrics,
                    optimizer=optimizer,
                )

    @property
    def model_dir(self) -> str:
        return self._model_dir

    @property
    def problem(self) -> Problem:
        return self._problem

    @property
    def pipeline(self) -> Pipeline:
        return self._pipeline

    def _get_datasets(self,
                      splits,
                      batch_size,
                      shuffle_buffer=None,
                      num_parallel_calls=tf.data.experimental.AUTOTUNE):
        problem = self.problem
        pipeline = self.pipeline

        def pre_batch_map(features, labels, weights=None):
            features = pipeline.pre_batch_map(features)
            return (features, labels) if weights is None else (features, labels,
                                                               weights)

        def post_batch_map(features, labels, weights=None):
            features = pipeline.post_batch_map(features)
            args = problem.post_batch_map(labels, weights)
            if isinstance(args, Sequence) and len(args) == 2:
                labels, weights = args
                return features, labels, weights
            else:
                return features, args

        def prep_dataset(split):
            dataset = problem.get_base_dataset(split=split)
            if split == 'train':
                dataset = dataset.shuffle(shuffle_buffer or
                                          problem.shuffle_buffer)
            dataset = dataset.repeat()
            dataset = dataset.map(pre_batch_map, num_parallel_calls)
            dataset = dataset.batch(batch_size)
            dataset = dataset.map(post_batch_map, num_parallel_calls)
            return dataset

        return tf.nest.map_structure(prep_dataset, splits)

    def fit(self,
            batch_size: int,
            epochs: int,
            shuffle_buffer: Optional[int] = None,
            verbose: bool = True,
            callbacks: Sequence[tf.keras.callbacks.Callback] = [],
            chkpt_kwargs: Mapping[str, Any] = {}):
        problem = self.problem
        pipeline = self.pipeline
        model_dir = self.model_dir

        splits = ('train', 'validation')
        train_ds, val_ds = self._get_datasets(splits, batch_size,
                                              shuffle_buffer)
        train_steps, val_steps = (
            problem.examples_per_epoch(split, batch_size) for split in splits)

        model = pipeline.model
        if not os.path.isdir(model_dir):
            os.makedirs(model_dir)
        chkpt_dir = os.path.join(model_dir, 'chkpts')
        chkpt_callback = cb.CheckpointCallback(directory=chkpt_dir,
                                               **chkpt_kwargs)

        chkpt_callback.set_model(model)
        initial_epoch = chkpt_callback.restore()
        if initial_epoch is None:
            initial_epoch = 0

        callbacks = [
            cb.AbslLogger(),
            tf.keras.callbacks.TerminateOnNaN(),
            chkpt_callback,
        ] + list(callbacks) + [
            cb.HPCallback(log_dir=model_dir),
            tf.keras.callbacks.TensorBoard(log_dir=model_dir,
                                           profile_batch=train_steps // 2),
        ]

        logging.info('Training starting with operative config: \n{}'.format(
            gin.operative_config_str()))
        model.summary(print_fn=logging.info)

        return model.fit(
            train_ds,
            epochs=epochs,
            verbose=verbose,
            steps_per_epoch=train_steps,
            validation_data=val_ds,
            validation_steps=val_steps,
            callbacks=callbacks,
            initial_epoch=initial_epoch,
        )

    def run_dataset(self,
                    batch_size: int,
                    num_examples: int = 10,
                    shuffle_buffer: Optional[int] = None,
                    split: Split = 'train',
                    num_parallel_calls: int = 1):
        from tqdm import tqdm
        logging.info('Running dataset')
        dataset = self._get_datasets(
            split,
            batch_size,
            shuffle_buffer,
            num_parallel_calls=num_parallel_calls).take(num_examples)
        if tf.executing_eagerly():
            for _ in tqdm(dataset, total=num_examples):
                pass
            # HACK
            # for example in tqdm(dataset, total=num_examples):
            #     print([x.numpy() for x in self._pipeline.model(example)])
        else:
            example = tf.compat.v1.data.make_one_shot_iterator(
                dataset).get_next()
            with tf.compat.v1.Session() as sess:
                for _ in tqdm(range(num_examples), total=num_examples):
                    sess.run(example)
        logging.info('Finished running dataset')


@gin.configurable(module='kb.framework')
def fit(trainable: Trainable,
        batch_size: int,
        epochs: int,
        shuffle_buffer: Optional[int] = None,
        verbose: bool = True,
        callbacks: Sequence[tf.keras.callbacks.Callback] = [],
        chkpt_kwargs: Mapping[str, Any] = {}):
    return trainable.fit(batch_size=batch_size,
                         epochs=epochs,
                         shuffle_buffer=shuffle_buffer,
                         verbose=verbose,
                         callbacks=callbacks,
                         chkpt_kwargs=chkpt_kwargs)


@gin.configurable(module='kb.framework')
def run_dataset(trainable: Trainable,
                batch_size: int,
                num_examples: int = 10,
                shuffle_buffer: Optional[int] = None,
                split: Split = 'train'):
    trainable.run_dataset(batch_size,
                          num_examples,
                          shuffle_buffer=shuffle_buffer,
                          split=split)
