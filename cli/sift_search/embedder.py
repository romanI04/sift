"""Compute embeddings using bge-small-en-v1.5.

Supports two providers:
  - local: ONNX via onnxruntime (default, free, no API key)
  - openai: OpenAI API text-embedding-3-small (requires OPENAI_API_KEY)
"""

import os
import numpy as np

EMBEDDING_DIM = 384
BATCH_SIZE = 32


class LocalEmbedder:
    """ONNX-based embedder using bge-small-en-v1.5 (quantized, 34MB)."""

    MODEL_REPO = "Xenova/bge-small-en-v1.5"
    MODEL_FILE = "onnx/model_quantized.onnx"
    TOKENIZER_FILE = "tokenizer.json"

    def __init__(self):
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        model_path = hf_hub_download(
            repo_id=self.MODEL_REPO, filename=self.MODEL_FILE
        )
        tokenizer_path = hf_hub_download(
            repo_id=self.MODEL_REPO, filename=self.TOKENIZER_FILE
        )

        self.session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_padding(pad_token="[PAD]", pad_id=0)
        self.tokenizer.enable_truncation(max_length=512)

    def embed(self, texts):
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

            hidden_states = outputs[0]
            mask = attention_mask[:, :, np.newaxis].astype(np.float32)
            pooled = np.sum(hidden_states * mask, axis=1) / np.clip(
                np.sum(mask, axis=1), a_min=1e-9, a_max=None
            )

            norms = np.linalg.norm(pooled, axis=1, keepdims=True)
            pooled = pooled / np.clip(norms, a_min=1e-9, a_max=None)

            all_embeddings.append(pooled)

        return np.concatenate(all_embeddings, axis=0).astype(np.float32)

    @property
    def model_name(self):
        return f"{self.MODEL_REPO}/{self.MODEL_FILE}"


class OpenAIEmbedder:
    """OpenAI API embedder using text-embedding-3-small at 384 dims."""

    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable required for --provider openai"
            )
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "Install openai package: pip install openai"
            )
        self.client = OpenAI(api_key=api_key)

    def embed(self, texts):
        all_embeddings = []

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
                dimensions=EMBEDDING_DIM,
            )
            vecs = [item.embedding for item in response.data]
            batch_np = np.array(vecs, dtype=np.float32)

            norms = np.linalg.norm(batch_np, axis=1, keepdims=True)
            batch_np = batch_np / np.clip(norms, a_min=1e-9, a_max=None)

            all_embeddings.append(batch_np)

        return np.concatenate(all_embeddings, axis=0).astype(np.float32)

    @property
    def model_name(self):
        return "openai/text-embedding-3-small"


class Embedder:
    """Factory that delegates to the right provider."""

    def __init__(self, provider="local"):
        if provider == "openai":
            self._impl = OpenAIEmbedder()
        else:
            self._impl = LocalEmbedder()

    def embed(self, texts):
        return self._impl.embed(texts)

    @property
    def model_name(self):
        return self._impl.model_name
