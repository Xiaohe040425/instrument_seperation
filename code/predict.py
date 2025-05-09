import json
import torch
from model import InstrumentBiLSTM  # 假設你模型存在 model.py
from torch.nn.utils.rnn import pad_sequence

# 樂器標籤對照
label_to_instrument = {0: "trumpet", 1: "trombone", 2: "tuba"}

# 載入模型
model = InstrumentBiLSTM(input_dim=4, hidden_dim=64, output_dim=3)
model.load_state_dict(torch.load("bilstm_model.pth"))  # 載入訓練後的模型
model.eval()

def predict_instruments_for_segment(segment_json_path):
    # 讀入 JSON
    with open(segment_json_path, 'r') as f:
        phrase = json.load(f)

    # 處理成 Tensor 格式
    features = torch.stack([
        torch.tensor([
            note["pitch_class"], note["octave"],
            note["duration"], note["position"]
        ], dtype=torch.float32) for note in phrase
    ]).unsqueeze(0)  # 增加 batch 維度

    lengths = torch.tensor([len(phrase)])

    with torch.no_grad():
        output = model(features, lengths)
        pred = torch.argmax(output, dim=2)[0]  # 取出 batch 內的第一組
        labels = [label_to_instrument[i.item()] for i in pred]

    # 配對結果
    assigned = []
    for note, label in zip(phrase, labels):
        note_with_label = note.copy()
        note_with_label["assigned_instrument"] = label
        assigned.append(note_with_label)

    return assigned

# 實際執行範例
if __name__ == "__main__":
    result = predict_instruments_for_segment("segment.json")
    print(json.dumps(result, indent=2, ensure_ascii=False))
