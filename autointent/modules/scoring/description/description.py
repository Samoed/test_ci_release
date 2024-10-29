import json
from pathlib import Path
from typing import TypedDict

import numpy as np
import scipy
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity

from autointent.context import Context
from autointent.context.vector_index_client import VectorIndex, VectorIndexClient
from autointent.modules.scoring.base import ScoringModule


class DescriptionScorerDumpMetadata(TypedDict):
    device: str
    db_dir: str
    n_classes: int
    multilabel: bool
    model_name: str


class DescriptionScorer(ScoringModule):
    metadata_dict_name: str = "metadata.json"
    weights_file_name: str = "description_vectors.npy"
    _vector_index: VectorIndex

    def __init__(self, temperature: float = 1.0) -> None:
        self.temperature = temperature

    def fit(self, context: Context) -> None:
        self._multilabel = context.multilabel
        self._vector_index = context.get_best_index()
        self._n_classes = context.n_classes

        descriptions = context.data_handler.label_description
        if any(description is None for description in descriptions):
            error_text = (
                "Some intent descriptions (label_description) are missing (None). "
                "Please ensure all intents have descriptions."
            )
            raise ValueError(error_text)

        self.description_vectors = self._vector_index.embedder.embed(
            [desc for desc in descriptions if desc is not None]
        )

        self.metadata = DescriptionScorerDumpMetadata(
            device=context.device,
            db_dir=context.db_dir,
            n_classes=self._n_classes,
            multilabel=self._multilabel,
            model_name=self._vector_index.model_name,
        )

    def predict(self, utterances: list[str]) -> NDArray[np.float64]:
        utterance_vectors = self._vector_index.embedder.embed(utterances)
        similarities: NDArray[np.float64] = cosine_similarity(utterance_vectors, self.description_vectors)

        if self._multilabel:
            probabilites = scipy.special.expit(similarities / self.temperature)
        else:
            probabilites = scipy.special.softmax(similarities / self.temperature, axis=1)
        return probabilites  # type: ignore[no-any-return]

    def clear_cache(self) -> None:
        self._vector_index.delete()

    def dump(self, path: str) -> None:
        dump_dir = Path(path)
        with (dump_dir / self.metadata_dict_name).open("w") as file:
            json.dump(self.metadata, file, indent=4)

        np.save(dump_dir / self.weights_file_name, self.description_vectors)

    def load(self, path: str) -> None:
        dump_dir = Path(path)

        self.description_vectors = np.load(dump_dir / self.weights_file_name)

        with (dump_dir / self.metadata_dict_name).open() as file:
            self.metadata = json.load(file)

        self._n_classes = self.metadata["n_classes"]
        self._multilabel = self.metadata["multilabel"]

        vector_index_client = VectorIndexClient(device=self.metadata["device"], db_dir=self.metadata["db_dir"])
        self._vector_index = vector_index_client.get_index(self.metadata["model_name"])
