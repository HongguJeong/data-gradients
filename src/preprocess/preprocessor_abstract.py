from abc import ABC, abstractmethod

from PIL.Image import Image
import numpy as np
import torch
from torchvision.transforms import transforms

from src import preprocess
from src.utils import SegBatchData


class PreprocessorAbstract(ABC):

    def __init__(self, num_classes=0):
        self.number_of_classes: int = num_classes
        self._number_of_channels: int = 3
        self._container_mapper = {"first": None, "second": None}

    @abstractmethod
    def validate(self, objects):
        pass

    @abstractmethod
    def preprocess(self, images, labels) -> SegBatchData:
        pass

    @property
    def route(self):
        route = {}
        if self._container_mapper['first'] is not None:
            route.update({'get images': self._container_mapper['first'].route})
        if self._container_mapper['second'] is not None:
            route.update({'get labels': self._container_mapper['second'].route})
        return route if route else None

    @staticmethod
    def channels_last_to_first(tensors: torch.Tensor):
        """
        Permute BS, W, H, C -> BS, C, W, H
                0   1  2  3 -> 0   3  1  2
        :param tensors: Tensor[BS, W, H, C]
        :return: Tensor[BS, C, W, H]
        """
        return tensors.permute(0, 3, 1, 2)

    def _to_tensor(self, objs, tuple_place: str = "") -> torch.Tensor:
        """

        :param objs:
        :param tuple_place:
        :return:
        """
        if isinstance(objs, np.ndarray):
            return torch.from_numpy(objs)
        elif isinstance(objs, Image):
            return transforms.ToTensor()(objs)
        else:
            return self._handle_dict(objs, tuple_place)

    def _handle_dict(self, objs, tuple_place):
        if self._container_mapper[tuple_place] is not None:
            return self._container_mapper[tuple_place].container_to_tensor(objs)
        else:
            self._container_mapper[tuple_place] = preprocess.ContainerMapper()
            self._container_mapper[tuple_place].images = tuple_place == 'first'
            self._container_mapper[tuple_place].analyze(objs)
            return self._container_mapper[tuple_place].container_to_tensor(objs)

