import time

from modules.rebuild_master import rebuild_master_criteria
from modules.normalize_projects import normalize_projects
from modules.calculate_project_scores import calculate_project_scores

SDG_MASTER_CRITERIA_FILE = "sdg_master_criteria.json"
SECTOR_MASTER_CRITERIA_FILE = "sector_master_criteria.json"

SECTORS = ["forestry"]
MAX_SCORE = 2


def run_pipeline():
    print("\n🚀 Minimal SDG Pipeline\n")

    start = time.time()

    # Step 1 — Build sector criteria
    rebuild_master_criteria(
        input_file_name=SDG_MASTER_CRITERIA_FILE,
        output_file_name=SECTOR_MASTER_CRITERIA_FILE
    )

    # Step 2 — Convert LLM → structured
    normalize_projects(
        sectors=SECTORS,
        master_criteria_file=SECTOR_MASTER_CRITERIA_FILE
    )

    # Step 3 — Compute final scores
    calculate_project_scores(
        sectors=SECTORS,
        master_criteria_file=SECTOR_MASTER_CRITERIA_FILE,
        max_score=MAX_SCORE
    )

    print(f"\n✅ Done in {round(time.time()-start, 2)}s\n")


if __name__ == "__main__":
    run_pipeline()