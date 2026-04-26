import json

from agents.judge_agent import JudgeAgent
from .config.settings import JUDGE_MODELS, TEMPERATURES, MAX_ROUNDS

class SDGJudgingBoard:
    def __init__(self):
        self.judges = [
            JudgeAgent(model, temp)
            for model, temp in zip(JUDGE_MODELS, TEMPERATURES)
        ]

        self.initial_prompt = open(
            "agents/prompts/initial_eval.txt"
        ).read()

        self.debate_prompt = open(
            "agents/prompts/debate_prompt.txt"
        ).read()
        self.summary_prompt = open(
            "agents/prompts/get_summary.txt"
        ).read()

    def _build_initial_prompt(self, query, evidences, context):
        return self.initial_prompt.format(
            original_query=query,
            evidences=evidences,
            context=context
        )

    def _build_debate_prompt(self, query, evidences, context, prev, others):
        return self.debate_prompt.format(
            original_query=query,
            evidences=evidences,
            context=context,
            your_previous_output=json.dumps(prev),
            other_judges_outputs=json.dumps(others)
        )
    
    def _majority_vote(self, results):
        """
        Returns:
            best_score (0,1,2)
            confidence (0–1)
            distribution (for debugging)
        """
        scores = [r["score"] for r in results if "score" in r]

        if not scores:
            return 0, 0.0, {}

        # Count votes
        vote_counts = {}
        for s in scores:
            vote_counts[s] = vote_counts.get(s, 0) + 1

        # Find majority score
        best_score = max(vote_counts, key=vote_counts.get)
        max_votes = vote_counts[best_score]

        # Confidence = agreement ratio
        confidence = max_votes / len(scores)

        return best_score, confidence, vote_counts
        
    def run(self, query, evidences, context):
        prompt = self._build_initial_prompt(query, evidences, context)

        # Round 1
        results = [j.initial_evaluate(prompt) for j in self.judges]

        best_score, best_confidence, _ = self._majority_vote(results)
        best_results = results

        no_improve_rounds = 0
        round_id = 1

        for round_id in range(2, MAX_ROUNDS + 1):
            new_results = []

            for i, judge in enumerate(self.judges):
                others = [
                    results[j]
                    for j in range(len(results)) if j != i
                ]

                debate_prompt = self._build_debate_prompt(
                    query, evidences, context,
                    results[i], others
                )

                new_results.append(judge.debate(debate_prompt))

            results = new_results

            score, confidence, distribution = self._majority_vote(results)

            improved = (
                confidence > best_confidence or
                (confidence == best_confidence and score == best_score)
            )

            if improved:
                best_score = score
                best_confidence = confidence
                best_results = results
                no_improve_rounds = 0
            else:
                no_improve_rounds += 1

            if best_confidence >= 0.75:
                break

            if no_improve_rounds >= 2:
                break

        return self._final_output(
            best_score,
            best_confidence,
            best_results
        )

    def _final_output(self, score, results, confident):
        result = "\n\n".join(
            f"[Summary: {r['summary']} | Justification: {r['justification']}]"
            for r in results
        )
        prompt = self.summary_prompt.format(
            score=score,
            result=result
        )
        summary = self.judges[0].get_summary(prompt=prompt)
        return {
            "score": score,
            "confidence": confident,
            "judgements": results,
            "summary": summary
        }