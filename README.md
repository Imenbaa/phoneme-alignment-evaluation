# Phoneme Alignment Evaluation

This repository provides tools to evaluate phoneme alignment systems using:

* Phoneme Error Rate (PER)
* Boundary F1 score
* Detection-based metrics (one-vs-rest phoneme evaluation)

## 📌 Features

* ETF format parsing (ESTER-style)
* PER computation using jiwer
* Boundary-based F1 with tolerance
* Per-style evaluation (spontaneous, read, etc.)
* Conversion from PKL to ETF format

## 📂 Input Format

ETF format:

```
<source> <channel> <start_time> <duration> <type> <subtype> <event> <score> <decision>
```

Example:

```
file.wav 1 0.45 0.07 sc - aa - t
```

## 🚀 Usage

### 1. Convert PKL to ETF

```bash
python scripts/pkl_to_etf.py --input data.pkl --output ref.etf
```

### 2. Run evaluation

```bash
python scripts/trackeval.py -r sum -b sum ref.etf hyp.etf
```

## 📊 Metrics

* PER (Phoneme Error Rate)
* Boundary F1 (tolerance-based)
* Detection metrics per phoneme

⚠️ Note: PER is computed in a one-vs-rest setting (no substitutions).

## 🧪 Example

Example files are provided in `data/example/`.

## 📌 TODO

* [ ] Add visualization
* [ ] Add confusion matrix
* [ ] Optimize ETF generation

## 👤 Author

Your Name
