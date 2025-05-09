# BiLSTM Instrument Assignment - Phrase-Level Support

import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence, pad_packed_sequence

# -------------------------------
# Configs and Label Mapping
# -------------------------------
instrument_labels = {"trumpet": 0, "trombone": 1, "tuba": 2}
label_to_instrument = {v: k for k, v in instrument_labels.items()}

# -------------------------------
# Dataset and Preprocessing
# -------------------------------
class PhraseDataset(Dataset):
    def __init__(self, phrase_path, label_path=None):
        with open(phrase_path, 'r') as f:
            self.phrases = json.load(f)
        if label_path:
            with open(label_path, 'r') as f:
                self.labels = json.load(f)
        else:
            self.labels = None

    def __len__(self):
        return len(self.phrases)

    def __getitem__(self, idx):
        phrase = self.phrases[idx]
        features = [torch.tensor([
            note["pitch_class"],
            note["octave"],
            note["duration"],
            note["position"]
        ], dtype=torch.float32) for note in phrase]

        if self.labels:
            label_seq = [torch.tensor(instrument_labels[l], dtype=torch.long) for l in self.labels[idx]]
            return torch.stack(features), torch.tensor(label_seq)
        else:
            return torch.stack(features)

# -------------------------------
# Collate Function for Padding
# -------------------------------
def collate_fn(batch):
    if isinstance(batch[0], tuple):
        sequences, labels = zip(*batch)
        lengths = torch.tensor([len(seq) for seq in sequences])
        padded_sequences = pad_sequence(sequences, batch_first=True)
        padded_labels = pad_sequence(labels, batch_first=True, padding_value=-100)  # ignore index
        return padded_sequences, padded_labels, lengths
    else:
        sequences = batch
        lengths = torch.tensor([len(seq) for seq in sequences])
        padded_sequences = pad_sequence(sequences, batch_first=True)
        return padded_sequences, lengths

# -------------------------------
# BiLSTM Model
# -------------------------------
class InstrumentBiLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers=2):
        super(InstrumentBiLSTM, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers,
                            bidirectional=True, batch_first=True)
        self.fc = nn.Linear(hidden_dim * 2, output_dim)

    def forward(self, x, lengths):
        packed = pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=False)
        out, _ = self.lstm(packed)
        out, _ = pad_packed_sequence(out, batch_first=True)
        out = self.fc(out)
        return out

# -------------------------------
# Training Function
# -------------------------------
def train(model, dataloader, epochs=10):
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss(ignore_index=-100)
    model.train()

    for epoch in range(epochs):
        total_loss = 0
        for X, y, lengths in dataloader:
            optimizer.zero_grad()
            outputs = model(X, lengths)
            loss = criterion(outputs.view(-1, outputs.shape[-1]), y.view(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1}: Loss = {total_loss:.4f}")

# -------------------------------
# Prediction Function
# -------------------------------
def predict(model, phrases):
    model.eval()
    with torch.no_grad():
        features = [torch.stack([
            torch.tensor([
                note["pitch_class"], note["octave"], note["duration"], note["position"]
            ], dtype=torch.float32) for note in phrase]) for phrase in phrases]

        lengths = torch.tensor([len(seq) for seq in features])
        padded = pad_sequence(features, batch_first=True)
        outputs = model(padded, lengths)
        predicted = torch.argmax(outputs, dim=2).tolist()

        result = []
        for i, length in enumerate(lengths):
            result.append([label_to_instrument[p] for p in predicted[i][:length]])
        return result

# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    phrase_path = "phrases.json"
    label_path = "phrase_labels.json"

    dataset = PhraseDataset(phrase_path, label_path)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=collate_fn)

    model = InstrumentBiLSTM(input_dim=4, hidden_dim=64, output_dim=3)
    train(model, dataloader, epochs=20)

    with open(phrase_path, 'r') as f:
        test_phrases = json.load(f)
    result = predict(model, test_phrases)
    print("Predicted instruments per phrase:", result)
