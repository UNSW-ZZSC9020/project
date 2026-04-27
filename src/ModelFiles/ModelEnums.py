# This module defines the enumeration types for different model architectures of the same model family used in the project.
# Note that not all enums were used in the project.
from enum import Enum

class LSTMModelType(str, Enum):
    LSTM = "lstm"
    BILSTM = "bilstm"
    MULTIHEAD_ATTENTION_LSTM = "multihead_attention_lstm"
    MULTIHEAD_ATTENTION_BILSTM = "multihead_attention_bilstm"

class TransformerModelType(str, Enum):
    PATCHTST = "patchtst"
    ITRANSFORMER = "itransformer"
    TIMEXER = "timexer"