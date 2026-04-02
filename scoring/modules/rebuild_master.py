import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = "sdg_master_criteria.json"
OUTPUT_FILE = "sector_master_criteria.json"
CRITERIA_DIRECTORY = "criteria"


def rebuild_master_criteria(input_file_name=None, output_file_name=None):

    input_file = input_file_name or INPUT_FILE
    output_file = output_file_name or OUTPUT_FILE

    input_path = os.path.join(BASE_DIR, CRITERIA_DIRECTORY, input_file)
    output_path = os.path.join(BASE_DIR, CRITERIA_DIRECTORY, output_file)

    with open(input_path, "r", encoding="utf-8") as f:
        original_master = json.load(f)

    sdgs = original_master.get("sdgs", {})

    new_master = {"sectors": {}}

    for sdg_id, sdg in sdgs.items():
        for target_id, target in sdg.get("targets", {}).items():

            for _, indicator in target.get("indicators", {}).items():

                for sector in indicator.get("sectors", []):
                    sector = sector.lower()

                    new_master["sectors"].setdefault(sector, {"sdgs": {}})

                    sector_sdgs = new_master["sectors"][sector]["sdgs"]

                    sector_sdgs.setdefault(sdg_id, {
                        "sdg_id": sdg_id,
                        "sdg_name": sdg.get("sdg_name"),
                        "targets": {}
                    })

                    sector_sdgs[sdg_id]["targets"].setdefault(target_id, {
                        "target_id": target_id,
                        "target_text": target.get("target_text"),
                        "indicators": []
                    })

                    sector_sdgs[sdg_id]["targets"][target_id]["indicators"].append({
                        "indicator_text": indicator.get("indicator_text"),
                        "description": indicator.get("description"),
                        "guidance": indicator.get("guidance"),
                        "data_unit": indicator.get("data_unit")
                    })

    # Assign IDs
    for sector in new_master["sectors"].values():
        for sdg in sector["sdgs"].values():
            for target in sdg["targets"].values():

                new_indicators = {}

                for idx, ind in enumerate(sorted(target["indicators"], key=lambda x: x["indicator_text"]), start=1):
                    ind_id = f"{target['target_id']}.i{idx}"
                    new_indicators[ind_id] = {
                        "indicator_id": ind_id,
                        "indicator_text": ind["indicator_text"],
                        "description": ind["description"],
                        "guidance": ind["guidance"],
                        "data_unit": ind["data_unit"]
                    }

                target["indicators"] = new_indicators

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_master, f, indent=4)

    print("✅ Master criteria rebuilt")