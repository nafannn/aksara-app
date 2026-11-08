"""CRNN + CTC (A3): CNN pengekstrak fitur -> BiLSTM -> logits per frame (blank = indeks 0)."""
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from .charset import NUM_CLASSES, decode_ids
from .config import IMG_H, IMG_W


def conv_block(x, ch):
    x = layers.Conv2D(ch, 3, padding="same", use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    return layers.ReLU()(x)


def build_model(width_mult: float = 1.0) -> keras.Model:
    c = lambda n: max(8, int(n * width_mult))
    inp = keras.Input((IMG_H, IMG_W, 1))
    x = conv_block(inp, c(16)); x = layers.MaxPool2D(2)(x)                 # H/2, W/2
    x = conv_block(x, c(32));   x = layers.MaxPool2D(2)(x)                 # H/4, W/4
    x = conv_block(x, c(64));   x = conv_block(x, c(64))
    x = layers.MaxPool2D((2, 1))(x)                                        # H/8, W/4
    x = conv_block(x, c(96));   x = layers.MaxPool2D((2, 1))(x)            # H/16, W/4
    t, h, ch = x.shape[2], x.shape[1], x.shape[3]
    x = layers.Permute((2, 1, 3))(x)                                       # (T, H', C)
    x = layers.Reshape((t, h * ch))(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Bidirectional(layers.LSTM(96, return_sequences=True))(x)
    out = layers.Dense(NUM_CLASSES)(x)                                     # logits
    return keras.Model(inp, out, name="aksara_crnn")


def ctc_loss(labels, label_len, logits):
    """labels: (B,L) int32 padded; label_len: (B,); logits: (B,T,C)."""
    T = tf.shape(logits)[1]
    logit_len = tf.fill([tf.shape(logits)[0]], T)
    loss = tf.nn.ctc_loss(labels, logits, label_len, logit_len,
                          logits_time_major=False, blank_index=0)
    return tf.where(tf.math.is_finite(loss), loss, tf.zeros_like(loss))   # abaikan sampel mustahil (label > T)


def greedy_decode(logits: np.ndarray):
    """logits (B,T,C) -> list[(teks, confidence)]. Confidence = rata-rata geometrik prob frame non-blank."""
    probs = tf.nn.softmax(logits, axis=-1).numpy()
    ids = probs.argmax(-1)
    out = []
    for p, seq in zip(probs, ids):
        chars, confs, prev = [], [], 0
        for t, k in enumerate(seq):
            if k != 0 and k != prev:
                chars.append(int(k)); confs.append(p[t, k])
            prev = k
        conf = float(np.exp(np.mean(np.log(np.clip(confs, 1e-8, 1))))) if confs else 0.0
        out.append((decode_ids(chars), conf))
    return out
