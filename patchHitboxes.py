import sys
import json

# equal in a gameplay-sense in the vast majority of cases i.e. the post-hit effect and whether they hit
def hitboxesEqual(hb1, hb2):
    fields = ["damage", "angle", "kb_growth", "weight_dep_kb", "hitbox_interaction",
        "base_kb", "element", "shield_damage", "hit_grounded", "hit_airborne"]
    for field in fields:
        if hb1[field] != hb2[field]:
            return False
    return True

with open(sys.argv[1]) as f:
    data = json.load(f)

with open(sys.argv[2], "r+b") as f:
    datFile = f.read()
    f.seek(0, 1)

    dataOffset = 0x20
    for i, subaction in enumerate(data["nodes"][0]["data"]["subactions"]):
        eventStrOffset = dataOffset + subaction["eventsOffset"]
        hitboxGuid = 0
        lastHitbox = None
        eventOffset = eventStrOffset
        for event in subaction["events"]:
            if "name" in event and event["name"] == "hitbox":
                if lastHitbox and not hitboxesEqual(lastHitbox, event["fields"]):
                    hitboxGuid += 1
                lastHitbox = event["fields"]

                # we are skipping the first bit of the damage field here
                # we don't want to set it anyways, but we also have to hope it's never 1
                damageOffset = eventOffset + 3

                print(event["bytes"])
                print(damageOffset, hitboxGuid)
                f.seek(damageOffset)
                f.write(bytes([hitboxGuid]))
            eventOffset += event["length"]
