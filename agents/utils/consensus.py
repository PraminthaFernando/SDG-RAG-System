def check_consensus(judgements):
    scores = [j["score"] for j in judgements]

    for s in set(scores):
        if scores.count(s) >= 2:
            return True, s

    return False, None