from typing import List

import cv2
import numpy as np

from src.feature_extractors.feature_extractor_abstract import FeatureExtractorAbstract
from src.logger.logger_utils import create_bar_plot


class AverageBrightness(FeatureExtractorAbstract):
    def __init__(self):
        super().__init__()
        self._brightness: List[float] = []
        self._luminance: List[float] = []

    def _execute(self, data):
        for image in data.images:
            np_image = image.numpy().transpose(1, 2, 0)
            lightness, _, _ = cv2.split(cv2.cvtColor(np_image, cv2.COLOR_BGR2LAB))
            n_lightness = lightness / np.max(lightness)
            self._brightness.append(np.mean(n_lightness))

    def process(self, ax, train):
        values, bins = np.histogram(self._brightness, bins=int(np.sqrt(len(self._brightness))))
        # values = [np.round(((100 * value) / sum(list(values))), 3) for value in values]
        new_keys = []
        for i, key in enumerate(bins):
            new = round(key, 2)
            if i == 0:
                continue
            elif i == 1:
                new_keys.append('<%.2f' % new)
            elif i == len(bins) - 1:
                new_keys.append('%.2f<' % new)
            else:
                new_keys.append('<%.2f<' % new)
        print(new_keys)
        print(values)
        create_bar_plot(ax, list(values), new_keys,
                        x_label="", y_label="% out of all images",
                        title="Average brightness of images", ticks_rotation=0,
                        train=train, color=self.colors[int(train)], yticks=True)

