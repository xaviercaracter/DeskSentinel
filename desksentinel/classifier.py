"""Fine-tune a small phishing classifier on a public Hub dataset.

Steps:
  1. Pick a phishing/spam email dataset on the Hub (search "phishing";
     choose one with 10k+ rows) and set DATASET_ID below.
  2. python -m desksentinel.classifier   (runs on CPU or your RTX 4060)

Outputs: ./classifier-out/ with the model + eval table printed to stdout.
Record the F1 in the README — that number is half the resume value.
"""
from __future__ import annotations

DATASET_ID = "SET_ME"          # e.g. search the Hub for a phishing email dataset
TEXT_COLUMN = "text"           # adjust to the dataset's column names
LABEL_COLUMN = "label"         # adjust: 1 = phishing, 0 = legitimate
OUTPUT_DIR = "classifier-out"


def main() -> None:
    import numpy as np
    from datasets import load_dataset
    from sklearn.metrics import precision_recall_fscore_support
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    if DATASET_ID == "SET_ME":
        raise SystemExit(
            "Set DATASET_ID in desksentinel/classifier.py to a real Hub dataset "
            "(search huggingface.co/datasets for 'phishing', 10k+ rows) and re-run."
        )

    ds = load_dataset(DATASET_ID)
    split = "train" if "train" in ds else list(ds.keys())[0]
    ds = ds[split].train_test_split(test_size=0.2, seed=42)

    tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    def tokenize(batch):
        return tok(batch[TEXT_COLUMN], truncation=True, padding="max_length", max_length=256)

    ds = ds.map(tokenize, batched=True)
    ds = ds.rename_column(LABEL_COLUMN, "labels")
    cols = ["input_ids", "attention_mask", "labels"]
    ds.set_format(type="torch", columns=cols)

    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=2
    )

    def metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=1)
        p, r, f, _ = precision_recall_fscore_support(labels, preds, average="binary", zero_division=0)
        return {"precision": p, "recall": r, "f1": f}

    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=64,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        logging_steps=100,
        seed=42,
    )

    trainer = Trainer(model=model, args=args, train_dataset=ds["train"],
                      eval_dataset=ds["test"], compute_metrics=metrics)
    trainer.train()
    print(trainer.evaluate())
    trainer.save_model(OUTPUT_DIR)
    print(f"Saved to ./{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
