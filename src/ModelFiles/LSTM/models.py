import torch
import torch.nn as nn

class SequenceForecaster(nn.Module):
    """
    Plain LSTM / Bi-LSTM forecaster using the final timestep output.
    Optionally uses an MLP head with ReLU.
    """
    def __init__(
        self,
        input_size,
        hidden_size,
        num_layers,
        horizon,
        forecast_last_step_only=True,
        dropout=0.0,
        bidirectional=False,
        use_mlp_head=False,
        mlp_hidden_size=32,
    ):
        super().__init__()

        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1
        self.use_mlp_head = use_mlp_head
        self.horizon = horizon
        self.forecast_last_step_only = forecast_last_step_only
        lstm_dropout = dropout if num_layers > 1 else 0.0

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
            bidirectional=bidirectional,
        )

        self.dropout = nn.Dropout(dropout)
        output_dim = hidden_size * self.num_directions

        if use_mlp_head:
            self.fc = nn.Sequential(
                nn.Linear(output_dim, mlp_hidden_size),
                nn.ReLU(),
                nn.Linear(mlp_hidden_size, horizon if not forecast_last_step_only else 1),
            )
        else:
            self.fc = nn.Linear(output_dim, horizon if not forecast_last_step_only else 1)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_out = lstm_out[:, -1, :]
        last_out = self.dropout(last_out)
        out = self.fc(last_out)
        if self.forecast_last_step_only:
            return out.view(-1)
        return out

class AttentionBiLSTMForecaster(nn.Module):
    """
    Bi-LSTM with attention over timesteps.
    Optionally uses an MLP head with ReLU.
    """
    def __init__(
        self,
        input_size,
        hidden_size,
        num_layers,
        horizon,
        forecast_last_step_only=True,
        dropout=0.0,
        bidirectional=True,
        use_mlp_head=False,
        mlp_hidden_size=32,
    ):
        super().__init__()

        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1
        self.use_mlp_head = use_mlp_head
        self.horizon = horizon
        self.forecast_last_step_only = forecast_last_step_only
        lstm_dropout = dropout if num_layers > 1 else 0.0
        output_dim = hidden_size * self.num_directions

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
            bidirectional=bidirectional,
        )

        self.attention = nn.Linear(output_dim, 1)
        self.dropout = nn.Dropout(dropout)

        if use_mlp_head:
            self.fc = nn.Sequential(
                nn.Linear(output_dim, mlp_hidden_size),
                nn.ReLU(),
                nn.Linear(mlp_hidden_size, horizon if not self.forecast_last_step_only else 1),
            )
        else:
            self.fc = nn.Linear(output_dim, horizon if not self.forecast_last_step_only else 1)

    def forward(self, x, return_attention=False):
        lstm_out, _ = self.lstm(x)
        attn_scores = self.attention(lstm_out) / (lstm_out.size(-1) ** 0.5)
        attn_weights = torch.softmax(attn_scores, dim=1)

        context = torch.sum(attn_weights * lstm_out, dim=1)
        context = self.dropout(context)

        out = self.fc(context)
        if self.forecast_last_step_only:
            out = out.view(-1)

        if return_attention:
            return out, attn_weights.squeeze(-1)

        return out
    
class MultiHeadAttentionBiLSTMForecaster(nn.Module):
    """
    Bi-LSTM with multi-head temporal attention over timesteps.
    Each head learns a separate attention distribution over the sequence.
    """
    def __init__(
        self,
        input_size,
        hidden_size,
        num_layers,
        horizon,
        forecast_last_step_only=True,
        dropout=0.0,
        bidirectional=True,
        use_mlp_head=False,
        mlp_hidden_size=32,
        num_attention_heads=4,
    ):
        super().__init__()

        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1
        self.num_attention_heads = num_attention_heads
        self.horizon = horizon
        self.forecast_last_step_only = forecast_last_step_only

        lstm_dropout = dropout if num_layers > 1 else 0.0
        output_dim = hidden_size * self.num_directions

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
            bidirectional=bidirectional,
        )

        # one score per head per timestep
        self.attention = nn.Linear(output_dim, num_attention_heads)
        self.dropout = nn.Dropout(dropout)

        combined_dim = output_dim * num_attention_heads

        if use_mlp_head:
            self.fc = nn.Sequential(
                nn.Linear(combined_dim, mlp_hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(mlp_hidden_size, horizon if not self.forecast_last_step_only else 1),
            )
        else:
            self.fc = nn.Linear(combined_dim, horizon if not self.forecast_last_step_only else 1)

    def forward(self, x, return_attention=False):
        # lstm_out: (batch, seq_len, output_dim)
        lstm_out, _ = self.lstm(x)

        # attn_scores: (batch, seq_len, num_heads)
        attn_scores = self.attention(lstm_out)

        # softmax over time dimension
        attn_weights = torch.softmax(attn_scores, dim=1)

        # reshape for broadcasting
        # lstm_out_expanded: (batch, seq_len, 1, output_dim)
        lstm_out_expanded = lstm_out.unsqueeze(2)

        # attn_weights_expanded: (batch, seq_len, num_heads, 1)
        attn_weights_expanded = attn_weights.unsqueeze(-1)

        # weighted sum over time
        # context: (batch, num_heads, output_dim)
        context = torch.sum(attn_weights_expanded * lstm_out_expanded, dim=1)

        # flatten heads
        # context: (batch, num_heads * output_dim)
        context = context.reshape(context.size(0), -1)
        context = self.dropout(context)

        out = self.fc(context)
        if self.forecast_last_step_only:
            out = out.view(-1)

        if return_attention:
            # return attention as (batch, num_heads, seq_len) for easier plotting
            return out, attn_weights.permute(0, 2, 1)

        return out