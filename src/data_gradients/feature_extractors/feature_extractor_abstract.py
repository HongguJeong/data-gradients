from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Tuple, Dict, Optional, List, Union

from matplotlib import pyplot as plt

from data_gradients.logging.logger import Logger
from data_gradients.logging.logger_utils import create_json_object, write_bar_ploit, write_heatmap_plot
from data_gradients.logging.results_logger import ResultsLogger
from data_gradients.utils.data_classes.batch_data import BatchData
from data_gradients.utils.data_classes.extractor_results import Results, HeatMapResults


class FeatureExtractorAbstract(ABC):
    """
    Main feature extractors class.
    Mandatory method to implement are execute() and process().
        * execute method will get a batch of data and will iterate over it to retrieve the features out of the data.
        * process will have some calculations over the features extracted in order to make it ready for histogram,
          plotting, etc.
    :param: colors - determine graph color for train/val bars
    :param: single_axis - determine if a graph should be combined axis train/val bars,
                          or have a separate axis for each of them.
    """
    def __init__(self):
        self.num_axis: Tuple[int, int] = (1, 1)
        self.colors: Dict[str, str] = {'train': 'green',
                                       'val': 'red'}

        # Logger data
        self.fig = None
        self.json_object: Dict[str, Optional[ResultsLogger]] = {'train': None, 'val': None}
        self.id_to_name = None

    def execute(self, data: BatchData):
        self._execute(data)

    @abstractmethod
    def _execute(self, data: BatchData):
        raise NotImplementedError

    def process(self, logger: Logger, id_to_name):
        self.id_to_name = id_to_name
        self.fig, ax = plt.subplots(*self.num_axis, figsize=(10, 5))

        for split in ['train', 'val']:
            results = self._post_process(split)
            self.write_results(results, ax)

        self.fig.tight_layout()
        logger.log(title_name=self.__class__.__name__, tb_data=self.fig, json_data=self.json_object)

    @abstractmethod
    def _post_process(self, split: str) -> Results:
        pass

    @abstractmethod
    def _process_data(self, split: str) -> Tuple[List, List]:
        pass

    def write_results(self, results: Union[Results, HeatMapResults], ax):
        if Resultsax_grid:
            ax.grid(visible=True, axis='y')

        if Resultsplot == 'bar-plot':
            write_bar_ploit(ax=ax,
                            results=results)
        elif Resultsplot == 'heat-map':
            # TODO: Make better way of splitting axis in same graph
            write_heatmap_plot(ax=ax[int(Resultssplit != 'train')],
                               results=results)
        else:
            raise NotImplementedError(f"Got plot key {Resultsplot}\
             while only supported plots are ['bar-plot', 'heat-map']")

        json_obj = create_json_object(Resultsjson_values if Resultsjson_values else Resultsvalues,
                                      Resultsbins if Resultsbins else Resultskeys)
        self.json_object.update({Resultssplit: json_obj})

    @staticmethod
    def merge_dict_splits(hist: Dict):
        for key in [*hist['train'], *hist['val']]:
            for split in [*hist]:
                if key not in list(hist[split].keys()):
                    # TODO: Fix value for not being always a 0 but might be a empty list instead
                    hist[split][key] = 0.
                hist[split] = OrderedDict(sorted(hist[split].items()))
