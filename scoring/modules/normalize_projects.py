import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_PARENT_FOLDERS = ["forestry"]
MASTER_CRITERIA_FILE = "sector_master_criteria.json"
PROJECT_SCORE_FILE = "nomic_sdg_prototype_llm_results.json"
OUTPUT_FILE = "structured_sdg_results.json"

CRITERIA_DIRECTORY = "criteria"
PROJECTS_DIRECTORY = "projects"


def normalize(text):
    return text.lower().strip() if text else ""


def normalize_projects(sectors=None, master_criteria_file=None):

    sectors = sectors or PROJECT_PARENT_FOLDERS
    master_criteria_file = master_criteria_file or MASTER_CRITERIA_FILE

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

            print(f"\n📂 {project}")

            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = {}

            for sdg_text, entries in data.items():

                try:
                    sdg_id, sdg_name = sdg_text.split(".", 1)
                except:
                    continue

                result.setdefault(sdg_id, {
                    "sdg_id": sdg_id,
                    "sdg_name": sdg_name.strip(),
                    "targets": {}
                })

                for e in entries:

                    target_text = e.get("target", "")
                    indicator_text = e.get("indicator", "")
                    score = e.get("score", 0)

                    if not target_text or not indicator_text:
                        continue

                    target_id = target_text.split(" ")[0]

                    matched_id = None

                    for s, s_data in master["sectors"].items():

                        if s != sector:
                            continue

                        for sdg_k, sdg_data in s_data["sdgs"].items():

                            if sdg_k != sdg_id:
                                continue

                            for t_k, t_data in sdg_data["targets"].items():

                                if t_k != target_id:
                                    continue

                                for ind_id, ind in t_data["indicators"].items():

                                    if normalize(indicator_text) == normalize(ind["indicator_text"]):
                                        matched_id = ind_id
                                        break

                    if not matched_id:
                        continue

                    target_obj = result[sdg_id]["targets"].setdefault(target_id, {
                        "target_id": target_id,
                        "target_text": target_text,
                        "indicators": {}
                    })

                    target_obj["indicators"][matched_id] = {
                        "indicator_id": matched_id,
                        "score": score
                    }

            output_file = os.path.join(project_path, OUTPUT_FILE)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"sdgs": result}, f, indent=4)

            print("✅ structured_sdg_results.json created")