from typing import Optional, Iterable, List, Dict

import hydra
from src.managers.abstract_manager import AnalysisManagerAbstract
from src.preprocess import SegmentationPreprocessor


class SegmentationAnalysisManager(AnalysisManagerAbstract):
    """
    Main semantic segmentation manager class.
    Definition of task name, task-related preprocessor and parsing related configuration file
    """
    TASK = "semantic_segmentation"

    def __init__(self, *, num_classes: int,
                 train_data: Iterable,
                 samples_to_visualize: int = 10,
                 ignore_labels: List[int] = None,
                 val_data: Optional[Iterable] = None,
                 id_to_name: Optional[Dict] = None,
                 ):
        """
        Constructor of semantic-segmentation manager which controls the analyzer
        :param num_classes: Number of valid classes to analyze
        :param train_data: Iterable object contains images and labels of the training dataset
        :param ignore_labels: List of not-valid labeled classes such as background.
        :param val_data: Iterable object contains images and labels of the validation dataset
        :param samples_to_visualize:
        :param class_id_to_name:
        """
        super().__init__(train_data, val_data, self.TASK, samples_to_visualize, id_to_name)

        self._preprocessor = SegmentationPreprocessor(num_classes, ignore_labels)

        self._parse_cfg()

    def _parse_cfg(self) -> None:
        """
        Parsing semantic segmentation configuration file with number of classes and ignore labels
        """
        hydra.initialize(config_path="../../config/", job_name="", version_base="1.1")
        self._cfg = hydra.compose(config_name=self._task)
        # TODO: Needs to disable strict mode
        self._cfg.number_of_classes = self._preprocessor.number_of_classes
        self._cfg.ignore_labels = self._preprocessor.ignore_labels
