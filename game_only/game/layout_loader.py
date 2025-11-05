import os
from game.config import SCORE_FILE

def load_layout(file_path):
    with open(file_path, 'r') as f:
        return [list(line.strip()) for line in f.readlines()]

def load_scores():
    if not os.path.exists(SCORE_FILE):
        return {}
    with open(SCORE_FILE, "r") as f:
        lines = f.readlines()
    return {line.split(":")[0].strip(): int(line.split(":")[1]) for line in lines if ":" in line}

def save_score(level_filename, score):
    scores = load_scores()
    best = scores.get(level_filename, -99999999)
    if score > best:
        scores[level_filename] = score
        with open(SCORE_FILE, "w") as f:
            for k, v in scores.items():
                f.write(f"{k}: {v}\n")
