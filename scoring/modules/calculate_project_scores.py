import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MASTER_FILE = "sector_master_criteria.json"
PROJECT_SCORE_FILE = "structured_sdg_results.json"

CRITERIA_DIRECTORY = "criteria"
PROJECTS_DIRECTORY = "projects"

OUTPUT_FILE_NAME = "project_impact_score.json"
MAX_INDICATOR_SCORE = 2


def calculate_project_scores(sectors=None, master_criteria_file=None, max_score=None):

    sectors = sectors or ["forestry"]
    master_criteria_file = master_criteria_file or MASTER_FILE
    max_score = max_score or MAX_INDICATOR_SCORE

    master_path = os.path.join(BASE_DIR, CRITERIA_DIRECTORY, master_criteria_file)

    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)

    for sector in sectors:

        sector_path = os.path.join(BASE_DIR, PROJECTS_DIRECTORY, sector)

        for project in os.listdir(sector_path):

            project_path = os.path.join(sector_path, project)

            if not os.path.isdir(project_path):
                continue

            input_file = os.path.join(project_path, PROJECT_SCORE_FILE)

            if not os.path.exists(input_file):
                continue

            print(f"Processing {project}")

            with open(input_file, "r", encoding="utf-8") as f:
                project_data = json.load(f)

            master_sdgs = master["sectors"][sector]["sdgs"]

            sdg_scores = {}
            sdg_values = []

            for sdg_id, sdg_data in master_sdgs.items():

                target_scores = []

                for target_id, target_data in sdg_data["targets"].items():

                    indicators = target_data["indicators"]
                    total = len(indicators)

                    if total == 0:
                        continue

                    score_sum = 0

                    for ind_id in indicators.keys():

                        val = (
                            project_data.get("sdgs", {})
                            .get(sdg_id, {})
                            .get("targets", {})
                            .get(target_id, {})
                            .get("indicators", {})
                            .get(ind_id, {})
                            .get("score", 0)
                        )

                        score_sum += min(val, max_score)

                    target_score = score_sum / (max_score * total)
                    target_scores.append(target_score)

                sdg_score = sum(target_scores) / len(target_scores) if target_scores else 0

                sdg_scores[sdg_id] = {
                    "score": sdg_score
                }

                sdg_values.append(sdg_score)

            final_score = sum(sdg_values) / len(sdg_values) if sdg_values else 0

            output = {
                "sector": sector,
                "final_score": final_score,
                "sdgs": sdg_scores
            }

            with open(os.path.join(project_path, OUTPUT_FILE_NAME), "w") as f:
                json.dump(output, f, indent=4)

            print("✅ project_impact_score.json created")