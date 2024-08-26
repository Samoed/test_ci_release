from typing import Callable

import numpy as np

from ..base import DataHandler, Module


class PredictionModule(Module):
    def fit(self, data_handler: DataHandler):
        raise NotImplementedError()

    def predict(self, scores: list[list[float]]):
        raise NotImplementedError()

    def score(self, data_handler: DataHandler, metric_fn: Callable) -> tuple[float, np.ndarray]:
        labels, scores = data_handler.get_prediction_evaluation_data()
        predictions = self.predict(scores)
        metric_value = metric_fn(labels, predictions)
        return metric_value, predictions

    def clear_cache(self):
        pass

    def _data_has_oos_samples(self, data_handler: DataHandler):
        return (data_handler.get_best_oos_scores() is not None)