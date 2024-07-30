from typing import Callable

import numpy as np

from .base import DataHandler, PredictionModule


class ThresholdModule(PredictionModule):
    def __init__(self, single_thresh: bool):
        self.signle_thresh = single_thresh

    def fit(self, data_handler: DataHandler):
        n_classes = data_handler.collection.metadata["n_classes"]
        self.thresh = 0.5 if self.signle_thresh else np.ones(n_classes) / 2

        # TODO: optimization

    def score(self, data_handler: DataHandler, metric_fn: Callable):
        predictions = self.predict(data_handler.scores)
        return metric_fn(data_handler.labels_test, predictions)

    def predict(self, scores: list[list[float]]):
        pred_classes = np.argmax(scores, axis=1)
        thresh = self.thresh if self.signle_thresh else self.thresh[pred_classes]
        best_scores = scores[np.arange(len(scores)), pred_classes]
        pred_classes[best_scores < thresh] = -1     # out of scope
        return pred_classes