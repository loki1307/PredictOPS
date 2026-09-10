"""
lstm_model.py — Shared pure-NumPy LSTM/GRU model definition.

Imported by both train.py (for training) and predictor.py (for inference).
Having it in a separate module ensures joblib can correctly unpickle the class.
"""

import numpy as np

RANDOM_SEED = 42


class _NumpyGRUCell:
    """
    Minimal GRU cell:
      z = sigmoid(Wz·[h,x] + bz)
      r = sigmoid(Wr·[h,x] + br)
      h̃ = tanh(Wh·[r*h, x] + bh)
      h = (1-z)*h + z*h̃
    """
    def __init__(self, input_size: int, hidden_size: int):
        scale = 0.1
        self.hidden_size = hidden_size
        total_in = input_size + hidden_size
        self.Wz = np.random.randn(hidden_size, total_in).astype(np.float32) * scale
        self.bz = np.zeros(hidden_size, dtype=np.float32)
        self.Wr = np.random.randn(hidden_size, total_in).astype(np.float32) * scale
        self.br = np.zeros(hidden_size, dtype=np.float32)
        self.Wh = np.random.randn(hidden_size, total_in).astype(np.float32) * scale
        self.bh = np.zeros(hidden_size, dtype=np.float32)

    @staticmethod
    def _sigmoid(x): return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))

    def forward(self, x: np.ndarray, h: np.ndarray) -> np.ndarray:
        """x: (batch, input_size), h: (batch, hidden_size) → h_new"""
        xh = np.concatenate([h, x], axis=1)
        z  = self._sigmoid(xh @ self.Wz.T + self.bz)
        r  = self._sigmoid(xh @ self.Wr.T + self.br)
        xh2 = np.concatenate([r * h, x], axis=1)
        h_tilde = np.tanh(xh2 @ self.Wh.T + self.bh)
        return (1.0 - z) * h + z * h_tilde


class MinimalLSTM:
    """
    Two-layer GRU + linear head for binary sequence classification.
    Pure NumPy — no TensorFlow, PyTorch, or other ML frameworks needed.

    API:
        model.fit(X_train, y_train, X_val, y_val, ...)
        model.predict(X)   → np.array of probabilities
    """

    def __init__(self, input_size: int, h1: int = 32, h2: int = 16):
        np.random.seed(RANDOM_SEED)
        self.input_size = input_size
        self.h1 = h1
        self.h2 = h2
        self.gru1   = _NumpyGRUCell(input_size, h1)
        self.gru2   = _NumpyGRUCell(h1, h2)
        self.W_out  = np.random.randn(1, h2).astype(np.float32) * 0.1
        self.b_out  = np.zeros(1, dtype=np.float32)

    @staticmethod
    def _sigmoid(x): return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))

    def _forward_sequence(self, X: np.ndarray) -> np.ndarray:
        """X: (batch, seq_len, features) → (batch,) probabilities."""
        batch = X.shape[0]
        h1 = np.zeros((batch, self.h1), dtype=np.float32)
        h2 = np.zeros((batch, self.h2), dtype=np.float32)
        for t in range(X.shape[1]):
            h1 = self.gru1.forward(X[:, t, :], h1)
            h2 = self.gru2.forward(h1, h2)
        logit = h2 @ self.W_out.T + self.b_out
        return self._sigmoid(logit).squeeze(1)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Inference: X (batch, seq_len, features) → (batch,) probabilities."""
        return self._forward_sequence(X)

    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            X_val: np.ndarray, y_val: np.ndarray,
            epochs: int = 60, batch_size: int = 64, lr: float = 0.01):

        import logging
        log = logging.getLogger("lstm_model")
        n             = len(X_train)
        best_val_loss = float('inf')
        best_W_out    = self.W_out.copy()
        best_b_out    = self.b_out.copy()
        patience      = 8
        patience_cnt  = 0

        for epoch in range(epochs):
            idx   = np.random.permutation(n)
            X_sh  = X_train[idx]
            y_sh  = y_train[idx]
            train_loss = 0.0

            for start in range(0, n, batch_size):
                xb = X_sh[start:start + batch_size]
                yb = y_sh[start:start + batch_size]

                # Forward
                p      = self._forward_sequence(xb)
                p_clip = np.clip(p, 1e-7, 1 - 1e-7)
                loss   = -(yb * np.log(p_clip) + (1 - yb) * np.log(1 - p_clip)).mean()
                train_loss += loss * len(xb)

                # Collect h2 for output-layer gradient
                batch2 = xb.shape[0]
                h1 = np.zeros((batch2, self.h1), dtype=np.float32)
                h2 = np.zeros((batch2, self.h2), dtype=np.float32)
                for t in range(xb.shape[1]):
                    h1 = self.gru1.forward(xb[:, t, :], h1)
                    h2 = self.gru2.forward(h1, h2)

                delta  = (p - yb)[:, None]
                dW     = delta.T @ h2 / batch2
                db     = delta.mean(axis=0)
                self.W_out -= lr * dW
                self.b_out -= lr * db

            train_loss /= n

            p_val      = self.predict(X_val)
            p_val_clip = np.clip(p_val, 1e-7, 1 - 1e-7)
            val_loss   = -(y_val * np.log(p_val_clip) + (1 - y_val) * np.log(1 - p_val_clip)).mean()
            val_acc    = ((p_val > 0.5) == (y_val > 0.5)).mean()

            log.info("Epoch %2d/%d  train_loss=%.4f  val_loss=%.4f  val_acc=%.4f",
                     epoch + 1, epochs, train_loss, val_loss, val_acc)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_W_out    = self.W_out.copy()
                best_b_out    = self.b_out.copy()
                patience_cnt  = 0
            else:
                patience_cnt += 1
                if patience_cnt >= patience:
                    log.info("Early stopping at epoch %d", epoch + 1)
                    break

        self.W_out = best_W_out
        self.b_out = best_b_out
        log.info("LSTM training done. Best val_loss=%.4f", best_val_loss)
