import concurrent
import itertools
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator, Iterable, Optional, List

import hydra
import tqdm
from matplotlib import pyplot as plt

from src.feature_extractors import FeatureExtractorAbstract
from src.logger.json_logger import JsonLogger
from src.logger.tensorboard_logger import TensorBoardLogger
from src.preprocess import PreprocessorAbstract
from src.utils import BatchData


# TODO: Check this out
# Itertools.chain(train, val) --> train0, train1, ..., trainN, val0, val1, ... valN
# Itertools.cycle(train) --> train0, train1, ... trainN, train0 , train1, ...
# Itertools.tee(train, n) --> iter(train[0, N/n]), iter(train[N/n, 2*(N/n)]), ... , iter(train[(n-1)*(N/n), N])

class AnalysisManagerAbstract:
    """
    Main dataset analyzer manager abstract class.
    """

    def __init__(self, train_data: Iterable,
                 val_data: Optional[Iterable],
                 task: str,
                 samples_to_visualize: int):

        self._train_extractors: List[FeatureExtractorAbstract] = []
        self._val_extractors: List[FeatureExtractorAbstract] = []

        self._threads = ThreadPoolExecutor()

        # TODO: Check if object has hasattr(bar, '__len__')
        self._dataset_size = len(train_data) if hasattr(train_data, '__len__') else None
        # Users Data Iterators
        self._train_iter: Iterator = train_data if isinstance(train_data, Iterator) else iter(train_data)
        if val_data is not None:
            self._train_only = False
            self._val_iter: Iterator = val_data if isinstance(val_data, Iterator) else iter(val_data)

        else:
            self._train_only = True
            self._val_iter = None

        # Logger
        self._loggers = {'TB': TensorBoardLogger(itertools.cycle(self._train_iter), samples_to_visualize),
                         'JSON': JsonLogger()}

        self._preprocessor: PreprocessorAbstract = Optional[None]
        self._cfg = None

        self._task = task

    def build(self):
        """
        Build method for hydra configuration file initialized and composed in manager constructor.
        Create lists of feature extractors, both to train and val iterables.
        """
        cfg = hydra.utils.instantiate(self._cfg)
        self._train_extractors = cfg.common + cfg[self._task]
        # Create another instances for same classes
        cfg = hydra.utils.instantiate(self._cfg)
        self._val_extractors = cfg.common + cfg[self._task]

    def _get_batch(self, data_iterator: Iterator) -> BatchData:
        """
        Iterates iterable, get a Tuple out of it, validate format and preprocess due to task preprocessor.
        :param data_iterator: Iterable for getting next item out of it
        :return: BatchData object, holding images, labels and preprocessed objects in accordance to task
        """
        batch = next(data_iterator)
        batch = tuple(batch) if isinstance(batch, list) else batch

        images, labels = self._preprocessor.validate(batch)

        bd = self._preprocessor.preprocess(images, labels)
        return bd

    def execute(self):
        return
        """
        Execute method take batch from train & val data iterables, submit a thread to it and runs the extractors.
        Method finish it work after both train & val iterables are exhausted.
        """
        pbar = tqdm.tqdm(desc='Working on batch # ', total=self._dataset_size)
        train_batch = 0
        val_batch_data = None
        # self._train_only = True
        while True:
            # total = time.time()
            if train_batch > 1000000:
                break
            try:
                # s = time.time()
                train_batch_data = self._get_batch(self._train_iter)
                # print()
                # print(f'Got train batch in {time.time() - s} seconds')
            except StopIteration:
                break
            else:
                pass

            if not self._train_only:
                try:
                    # s = time.time()
                    val_batch_data = self._get_batch(self._val_iter)
                    # print()
                    # print(f'Got val batch in {time.time() - s} seconds')
                except StopIteration:
                    self._train_only = True
                else:
                    pass
            # s = time.time()
            futures = [self._threads.submit(extractor.execute, train_batch_data) for extractor in
                       self._train_extractors]
            if not self._train_only:
                futures += [self._threads.submit(extractor.execute, val_batch_data) for extractor in
                            self._val_extractors]
            # print()
            # print(f'Submitted all threads in {time.time() -s} seconds')
            # Wait for all threads to finish
            # s = time.time()
            concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
            # print()
            # print(f'Finished all features in {time.time() - s} seconds')
            # print()
            # print(f'Total time for batch of {len(train_batch_data.images)} - {time.time() - total}')
            pbar.update()
            train_batch += 1

    def post_process(self):
        """
        Post process method runs on all feature extractors, concurrently on valid and train extractors, send each
        of them a matplotlib ax(es) and gets in return the ax filled with the feature extractor information.
        Then, it logs the information through the logger.
        :return:
        """
        self._loggers['TB'].visualize()

        for val_extractor, train_extractor in zip(self._val_extractors, self._train_extractors):
            axes = dict()
            if train_extractor.single_axis:
                fig, ax = plt.subplots(figsize=(10, 5))
                axes['train'] = axes['val'] = ax
            else:
                fig, ax = plt.subplots(1, 2, figsize=(10, 5))
                axes['train'], axes['val'] = ax

            # First val - because graph params will be overwritten by latest (train) and we want it's params
            val_hist = val_extractor.process(axes['val'], train=False)

            train_hist = train_extractor.process(axes['train'], train=True)

            fig.tight_layout()

            title = val_extractor.__class__.__name__
            self._loggers['TB'].log(title, fig)
            self._loggers['JSON'].log(title, [train_hist, val_hist])

    def close(self):
        """
        Safe logger closing
        """
        [self._loggers[logger].close() for logger in self._loggers.keys()]
        print(f'{"*" * 50}'
              f'\nWe have finished evaluating your dataset!'
              f'\nThe results can be seen in {self._loggers["TB"].logdir}')

    def run(self):
        """
        Run method activating build, execute, post process and close the manager.
        """
        self.build()
        self.execute()
        self.post_process()
        self.close()
