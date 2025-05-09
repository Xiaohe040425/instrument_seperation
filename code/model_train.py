# Simple BiLSTM Model for Instrument Classification

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence, pad_packed_sequence
import json

# ----------------------
# Label Mapping
# ----------------------
instrument_labels = {"trumpet": 0, "trombone": 1, "tuba": 2}
label_to_instrument = {v: k for k, v in instrument_labels.items()}

# ----------------------
# Dataset
# ----------------------
class MusicDataset(Dataset):
    def __init__(self, phrases_path, labels_path):
        with open(phrases_path) as f:
            self.phrases = json.load(f)
        with open(labels_path) as f:
            self.labels = json.load(f)

    def __len__(self):
        return len(self.phrases)

    def __getitem__(self, idx):
        phrase = [torch.tensor([note['pitch_class'], note['octave'], note['duration'], note['position']], dtype=torch.float32)
                  for note in self.phrases[idx]]
        label = [instrument_labels[name] for name in self.labels[idx]]
        return torch.stack(phrase), torch.tensor(label)

# ----------------------
# Collate Function
# ----------------------
def collate_fn(batch):
    phrases, labels = zip(*batch)
    lengths = torch.tensor([len(seq) for seq in phrases])
    padded_phrases = pad_sequence(phrases, batch_first=True)
    padded_labels = pad_sequence(labels, batch_first=True, padding_value=-100)
    return padded_phrases, padded_labels, lengths

# ----------------------
# BiLSTM Model
# ----------------------
class BiLSTMClassifier(nn.Module):
    def __init__(self, input_size=4, hidden_size=64, output_size=3):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_size * 2, output_size)

    def forward(self, x, lengths):
        packed = pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=False)
        out, _ = self.lstm(packed)
        out, _ = pad_packed_sequence(out, batch_first=True)
        out = self.fc(out)
        return out

# ----------------------
# Training
# ----------------------
def train(model, dataloader, epochs=10):
    model.train()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss(ignore_index=-100)

    for epoch in range(epochs):
        total_loss = 0
        for X, y, lengths in dataloader:
            optimizer.zero_grad()
            out = model(X, lengths)
            loss = criterion(out.view(-1, out.shape[-1]), y.view(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1} Loss: {total_loss:.4f}")

# ----------------------
# Prediction
# ----------------------
def predict(model, phrases):
    model.eval()
    with torch.no_grad():
        sequences = [torch.tensor([[note['pitch_class'], note['octave'], note['duration'], note['position']]
                                   for note in phrase], dtype=torch.float32) for phrase in phrases]
        lengths = torch.tensor([len(seq) for seq in sequences])
        padded = pad_sequence(sequences, batch_first=True)
        out = model(padded, lengths)
        pred = torch.argmax(out, dim=2)
        return [[label_to_instrument[i.item()] for i in seq[:l]] for seq, l in zip(pred, lengths)]
