"""Compute embeddings using all-MiniLM-L6-v2 ONNX via onnxruntime."""

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

MODEL_REPO = "Xenova/all-MiniLM-L6-v2"
MODEL_FILE = "onnx/model_quantized.onnx"
TOKENIZER_FILE = "tokenizer.json"
EMBEDDING_DIM = 384
BATCH_SIZE = 32


class Embedder:
    def __init__(self):
        model_path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE)
        tokenizer_path = hf_hub_download(repo_id=MODEL_REPO, filename=TOKENIZER_FILE)

        self.session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_padding(pad_token="[PAD]", pad_id=0)
        self.tokenizer.enable_truncation(max_length=256)

    def embed(self, texts):
        """Compute normalized embeddings for a list of texts.

        Returns numpy array of shape (len(texts), 384), float32.
        """
        all_embeddings = []

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            encodings = self.tokenizer.encode_batch(batch)

            input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
            attention_mask = np.array(
                [e.attention_mask for e in encodings], dtype=np.int64
            )

            token_type_ids = np.zeros_like(input_ids)

            outputs = self.session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                },
            )

            # Mean pooling
            hidden_states = outputs[0]  # (batch, seq_len, 384)
            mask = attention_mask[:, :, np.newaxis].astype(np.float32)
            pooled = np.sum(hidden_states * mask, axis=1) / np.clip(
                np.sum(mask, axis=1), a_min=1e-9, a_max=None
            )

            # L2 normalize
            norms = np.linalg.norm(pooled, axis=1, keepdims=True)
            pooled = pooled / np.clip(norms, a_min=1e-9, a_max=None)

            all_embeddings.append(pooled)

        return np.concatenate(all_embeddings, axis=0).astype(np.float32)

    @property
    def model_name(self):
        return f"{MODEL_REPO}/{MODEL_FILE}"
