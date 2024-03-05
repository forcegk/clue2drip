import json
import sys
from pprint import pprint
from datetime import datetime


BASE_NOTE = f"(C) {datetime.now().year} FGK Clue import script. Not imported fields: "

CSV_FIELDS = ["date","temperature.value","temperature.exclude","temperature.time","temperature.note","bleeding.value","bleeding.exclude","mucus.feeling","mucus.texture","mucus.value","mucus.exclude","cervix.opening","cervix.firmness","cervix.position","cervix.exclude","note.value","desire.value","sex.solo","sex.partner","sex.condom","sex.pill","sex.iud","sex.patch","sex.ring","sex.implant","sex.diaphragm","sex.none","sex.other","sex.note","pain.cramps","pain.ovulationPain","pain.headache","pain.backache","pain.nausea","pain.tenderBreasts","pain.migraine","pain.other","pain.note","mood.happy","mood.sad","mood.stressed","mood.balanced","mood.fine","mood.anxious","mood.energetic","mood.fatigue","mood.angry","mood.other","mood.note"]

def process(data):
    print("Processing data...")

    event_dict = {}

    for entry in data:
        event_dict[entry["date"]] = {}
        event_dict[entry["date"]]["note.value"] = ""
    
    for entry in data:
        match entry["type"]:
            case "discharge":
                # The mucus.value has some sort of algorithm that we can not calculate accurately.
                # I have put the values not randomly, but based on the description of the options.
                event_dict[entry["date"]]["mucus.feeling"] = 1
                event_dict[entry["date"]]["mucus.value"] = 3

                # For that reason, I will set to exclude the mucus value
                event_dict[entry["date"]]["mucus.exclude"] = "true"

                match entry["value"][0]["option"]:
                    case "egg_white":
                        event_dict[entry["date"]]["mucus.texture"] = 2
                    case "creamy":
                        event_dict[entry["date"]]["mucus.texture"] = 1
                    case "sticky":
                        event_dict[entry["date"]]["mucus.texture"] = 0
                        event_dict[entry["date"]]["mucus.value"] = 2
                    case "atypical":
                        event_dict[entry["date"]]["mucus.texture"] = 0
                        event_dict[entry["date"]]["mucus.value"] = 1
                    case _:
                        event_dict[entry["date"]]["mucus.texture"] = 0
            case "energy" | "feelings" | "mind":
                event_dict[entry["date"]]["mood.note"] = ""
                for inner_entry in entry["value"]:
                    event_dict[entry["date"]]["mood.note"] += inner_entry["option"] + ", "
                    match inner_entry["option"]:
                        case "exhausted":
                            event_dict[entry["date"]]["mood.fatigue"] = "true"
                        case "energetic":
                            event_dict[entry["date"]]["mood.energetic"] = "true"
                        case "tired":
                            event_dict[entry["date"]]["mood.fatigue"] = "true"
                        case "happy":
                            event_dict[entry["date"]]["mood.happy"] = "true"
                        case "sad":
                            event_dict[entry["date"]]["mood.sad"] = "true"
                        case "stressed":
                            event_dict[entry["date"]]["mood.stressed"] = "true"
                        case _:
                            event_dict[entry["date"]]["mood.other"] = "true"

                if "mood.other" in event_dict[entry["date"]]:
                    event_dict[entry["date"]]["mood.note"] = event_dict[entry["date"]]["mood.note"][:-2]
                else: 
                    # remove mood.note
                    del event_dict[entry["date"]]["mood.note"]
            case "pain":
                event_dict[entry["date"]]["pain.note"] = ""
                for inner_entry in entry["value"]:
                    event_dict[entry["date"]]["pain.note"] += inner_entry["option"] + ", "
                    match inner_entry["option"]:
                        case "breast_tenderness":
                            event_dict[entry["date"]]["pain.tenderBreasts"] = "true"
                        case "period_cramps":
                            event_dict[entry["date"]]["pain.cramps"] = "true"
                        case "ovulation":
                            event_dict[entry["date"]]["pain.ovulationPain"] = "true"
                        case "headache":
                            event_dict[entry["date"]]["pain.headache"] = "true"
                        case _:
                            event_dict[entry["date"]]["pain.other"] = "true"

                if "pain.other" in event_dict[entry["date"]]:
                    event_dict[entry["date"]]["pain.note"] = event_dict[entry["date"]]["pain.note"][:-2]
                else: 
                    # remove pain.note
                    del event_dict[entry["date"]]["pain.note"]
            case "period":
                event_dict[entry["date"]]["bleeding.exclude"] = "false"
                match entry["value"]["option"]:
                    case "heavy":
                        event_dict[entry["date"]]["bleeding.value"] = 3
                    case "medium":
                        event_dict[entry["date"]]["bleeding.value"] = 2
                    case "light":
                        event_dict[entry["date"]]["bleeding.value"] = 1
                    case _:
                        # tf did you do to end up here
                        raise NotImplementedError("Another value for period value??? Fixme")
            case "sex_life":
                event_dict[entry["date"]]["sex.note"] = "Manually set the method for: "
                event_dict[entry["date"]]["sex.partner"] = "true"
                for inner_entry in entry["value"]:
                    event_dict[entry["date"]]["sex.note"] += inner_entry["option"] + ", "
                    match inner_entry["option"]:
                        case "unprotected":
                            event_dict[entry["date"]]["sex.none"] = "true"
                        # case "protected":
                        # case "withdrawal":
                        # There is no option for method, so will mark other and note it
                        case _:
                            event_dict[entry["date"]]["sex.other"] = "true"

                if "sex.other" in event_dict[entry["date"]]:
                    event_dict[entry["date"]]["sex.note"] = event_dict[entry["date"]]["sex.note"][:-2]
                else: 
                    # remove sex.note
                    del event_dict[entry["date"]]["sex.note"]
            case "spotting":
                event_dict[entry["date"]]["bleeding.exclude"] = "false"
                event_dict[entry["date"]]["bleeding.value"] = 0
            case "birth_control_pill":
                if entry["value"]["option"] == "taken":
                    event_dict[entry["date"]]["sex.pill"] = "true"
                else:
                    raise NotImplementedError("Birth control pill not taken??? Fixme")
                
            case "tags" | "sleep_duration" | "social_life" | "collection_method" | "pms" | "craving" | "exercise" | "skin" | "stool":
                # check if entry["value"] is a list
                if event_dict[entry["date"]]["note.value"] != "":
                    event_dict[entry["date"]]["note.value"] += "  &  "
                
                event_dict[entry["date"]]["note.value"] += entry["type"] + ": "
                if isinstance(entry["value"], list):
                    for inner_entry in entry["value"]:
                        event_dict[entry["date"]]["note.value"] += inner_entry["option"] + ", "
                    event_dict[entry["date"]]["note.value"] = event_dict[entry["date"]]["note.value"][:-2]
                else:
                    event_dict[entry["date"]]["note.value"] = f"{entry["value"]}"[1:-1]
            case _:
                print(f"Unknown entry type: {entry['type']}")
                raise NotImplementedError("Unknown entry type??? Fixme")
        # event_dict[entry["date"][]] = 
    
    # Delete note.value if it's empty
    for key in event_dict:
        if event_dict[key]["note.value"] == "":
            del event_dict[key]["note.value"]
        else:
            event_dict[key]["note.value"] = BASE_NOTE + event_dict[key]["note.value"]

    pprint(event_dict)

    return event_dict

def dump_csv(data_dict, output_file_path):
    print("Dumping to CSV...")
    with open(output_file_path, 'w') as f:
        f.write(",".join(CSV_FIELDS) + "\n")
        for key in data_dict:
            f.write(f"{key}")
            for field in CSV_FIELDS[1:]:
                if field in data_dict[key]:
                    # Check if it ends with .note
                    if field == "note.value" or field.endswith(".note"):
                        f.write(f",\"{data_dict[key][field]}\"")
                    else:
                        f.write(f",{data_dict[key][field]}")
                else:
                    f.write(",")
            f.write("\n")

if __name__ == "__main__":
    # Check arguments and print usage if incorrect
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_json_file> <output_csv_file>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    output_file_path = sys.argv[2]

    with open(json_file_path, 'r') as f:
        json_data = json.load(f)
    
    data_dict = process(json_data)

    dump_csv(data_dict, output_file_path)
