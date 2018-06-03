import argparse
from collections import OrderedDict as odict
import json
import math
import sys

from prettyPrint import printAttackSummary
from specialSubactions import specialSubactions

attackMapping = odict([
    ("jab1", 0x2e),
    ("jab2", 0x2f),
    ("jab3", 0x30),
    ("rapidjabs_start", 0x31),
    ("rapidjabs_loop", 0x32),
    ("rapidjabs_end", 0x33),
    ("dashattack", 0x34),
    ("ftilt_h", 0x35),
    ("ftilt_mh", 0x36),
    ("ftilt_m", 0x37),
    ("ftilt_ml", 0x38),
    ("ftilt_l", 0x39),
    ("utilt", 0x3a),
    ("dtilt", 0x3b),
    ("fsmash_h", 0x3c),
    ("fsmash_mh", 0x3d),
    ("fsmash_m", 0x3e),
    ("fsmash_ml", 0x3f),
    ("fsmash_l", 0x40),
    ("usmash", 0x42),
    ("dsmash", 0x43),
    ("nair", 0x44),
    ("fair", 0x45),
    ("bair", 0x46),
    ("uair", 0x47),
    ("dair", 0x48),
    ("grab", 0xF2),
    ("dashgrab", 0xF3),
    ("pummel", 0xF5),
    ("fthrow", 0xf7),
    ("bthrow", 0xf8),
    ("uthrow", 0xf9),
    ("dthrow", 0xfa),
])

specialStartIndex = 0x127

class Hitbox(object):
    uniqueHitboxes = [] # unique in the sense of "sameEffect"
    allHitboxes = []

    def __init__(self, hitboxJson):
        self.guid = len(Hitbox.allHitboxes)
        Hitbox.allHitboxes.append(self)

        self.id = hitboxJson["id"]
        self.bone = hitboxJson["bone"]
        self.damage = hitboxJson["damage"]

        self.size = hitboxJson["size"]
        self.x, self.y, self.z = hitboxJson["x"], hitboxJson["y"], hitboxJson["z"]

        self.angle = hitboxJson["angle"]
        self.kbGrowth = hitboxJson["kbGrowth"]
        self.weightDepKb = hitboxJson["weightDepKb"]
        self.hitboxInteraction = hitboxJson["hitboxInteraction"]
        self.baseKb = hitboxJson["baseKb"]

        self.element = hitboxJson["element"]
        self.shieldDamage = hitboxJson["shieldDamage"]
        self.sfx = hitboxJson["sfx"]
        self.hitGrounded = hitboxJson["hitGrounded"]
        self.hitAirborne = hitboxJson["hitAirborne"]

        for i, other in enumerate(Hitbox.uniqueHitboxes):
            if self.sameEffect(other):
                self.groupId = other.groupId
                break
        else:
            self.groupId = len(Hitbox.uniqueHitboxes)
            Hitbox.uniqueHitboxes.append(self)

    # equal in a gameplay-sense in the vast majority of cases
    # "functionally the same" - the post-hit effect and whether they hit is the same
    def sameEffect(self, other):
        attrs = ["damage", "angle", "kbGrowth", "weightDepKb", "hitboxInteraction",
            "baseKb", "element", "shieldDamage", "hitGrounded", "hitAirborne"]
        for attr in attrs:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def toJsonDict(self):
        return odict([
            ("id", self.id),
            ("bone", self.bone),
            ("damage", self.damage),
            ("size", self.size),
            ("x", self.x),
            ("y", self.y),
            ("z", self.z),
            ("angle", self.angle),
            ("kbGrowth", self.kbGrowth),
            ("weightDepKb", self.weightDepKb),
            ("hitboxInteraction", self.hitboxInteraction),
            ("baseKb", self.baseKb),
            ("element", self.element),
            ("shieldDamage", self.shieldDamage),
            ("sfx", self.sfx),
            ("hitGrounded", self.hitGrounded),
            ("hitAirborne", self.hitAirborne),
            ("guid", self.guid),
            ("groupId", self.groupId),
        ])

    def toJsonDict_onlyEffect(self):
        return odict([
            ("damage", self.damage),
            ("angle", self.angle),
            ("kbGrowth", self.kbGrowth),
            ("weightDepKb", self.weightDepKb),
            ("hitboxInteraction", self.hitboxInteraction),
            ("baseKb", self.baseKb),
            ("element", self.element),
            ("shieldDamage", self.shieldDamage),
            ("hitGrounded", self.hitGrounded),
            ("hitAirborne", self.hitAirborne),
        ])

class Throw(object):
    def __init__(self, throwJson):

        self.damage = throwJson["damage"]
        self.angle = throwJson["angle"]
        self.kbGrowth = throwJson["kbGrowth"]
        self.weightDepKb = throwJson["weightDepKb"]
        self.baseKb = throwJson["baseKb"]
        self.element = throwJson["element"]

        # This will be set to true upon encountering the second throw command
        # and used for validation
        self.released = False

    def toJsonDict(self):
        ret = odict([
            ("damage", self.damage),
            ("angle", self.angle),
            ("kbGrowth", self.kbGrowth),
            ("weightDepKb", self.weightDepKb),
            ("baseKb", self.baseKb),
            ("element", self.element),
        ])
        if not self.released:
            ret["released"] = False
        return ret

class FrameInfo(object):
    def __init__(self, canAutocancel, canIasa, chargeFrame, projectile, activeHitboxes, throw=None):
        self.canAutocancel = canAutocancel
        self.canIasa = canIasa
        self.hitboxes = odict()
        self.chargeFrame = chargeFrame
        self.projectile = projectile

        for hitboxId in activeHitboxes:
            self.hitboxes[hitboxId] = activeHitboxes[hitboxId]

        self.throw = throw
        if self.throw and not throw.released:
            print("Unreleased throw!")

# This whole function is maybe super weird, but it's too much of a hassle to get rid of now
def getFrameData(events, totalFrames, airNormal):
    ignoreEvents = ["exit", "gfx", "rumble", "sfx", "continuationControl?",
        "randomSmashSfx", "reverseDirection", "animateTexture", "swordTrail",
        "bodyaura", "adjustHitboxSize", "animateModel", "pseudoRandomSfx"]

    # in case this got called multiple times
    Hitbox.uniqueHitboxes = []
    Hitbox.allHitboxes = []

    activeHitboxes = odict()
    canAutocancel = airNormal
    canIasa = False
    isGrabAttack = False
    frame = 1
    frameData = []
    waitUntil = 0
    currentEvent = 0
    loopStart = None
    loopCounter = 0
    while True: # frames
        chargeFrame = False
        throw = None
        projectile = False

        if frame < waitUntil:
            pass
        else:
            while currentEvent < len(events): # events
                event = events[currentEvent]
                eName = event.get("name", None)
                eFields = event["fields"] if "fields" in event else None
                currentEvent += 1

                if eName == "waitUntil":
                    waitUntil = eFields["frame"]
                    break
                elif eName == "waitFor":
                    waitUntil = frame + eFields["frames"]
                    break
                elif eName == "autocancel":
                    canAutocancel = not canAutocancel
                elif eName == "allowIasa":
                    canIasa = True
                elif eName == "endOneCollision":
                    activeHitboxes.pop(eFields["hitboxId"])
                elif eName == "endAllCollisions":
                    activeHitboxes = odict()
                elif eName == "hitbox":
                    activeHitboxes[eFields["id"]] = Hitbox(eFields)
                    if eFields["element"] == "grab":
                        isGrabAttack = True
                elif eName == "adjustHitboxDamage":
                    hitboxId = eFields["hitboxId"]
                    # This is not an assert, because some attacks (e.g. Link's AttackAirHi (uair))
                    # adjust the damage for hitboxes that are not active
                    # I am not 100% sure how to handle it correctly, but I assume it's fine to just ignore it
                    if hitboxId in activeHitboxes:
                        activeHitboxes[hitboxId] = Hitbox(activeHitboxes[hitboxId].toJsonDict())
                        activeHitboxes[hitboxId].damage = eFields["damage"]
                    else:
                        print("Adjust damage for non-active hitbox {}!".format(hitboxId))
                elif eName == "throw":
                    # Throw commands always come in pairs.
                    # The first has all the damage/knockback data (throwType = 0)
                    # The second makes sure the throw is released (throwType = 1),
                    #   not sure what damage/knockback/etc. means for the throwType = 1
                    if eFields["throwType"] == 0:
                        assert throw == None, "Second throw!"
                        throw = Throw(eFields)
                    else: # == 1
                        if throw:
                            throw.released = True
                        else:
                            # grabs have a throw release command after their hitboxes
                            # I don't know why and no one I asked knows why.
                            # If you are reading this and know it, tell me!
                            print("Unmatched throw release (1) command!")
                elif eName == "startSmashCharge":
                    chargeFrame = True
                elif eName == "shootitem":
                    projectile = True
                elif eName == "setLoop":
                    loopCounter = eFields["loopCount"]
                    loopStart = currentEvent
                elif eName == "executeLoop":
                    if loopCounter > 0:
                        loopCounter -= 1
                        currentEvent = loopStart
                elif eName == "return":
                    # Sometimes in the middle of a subaction (specials)
                    # a couple of return commands may appear
                    # I assume this is because parts of the subaction are used as subroutines/goto targets
                    # So for regular execution these commands are probably just ignored.
                    # Maybe not though, I didn't test it. If you know better, tell me!
                    pass
                elif eName in ignoreEvents:
                    pass
                else:
                    print("Unhandled event: {} ({}) on frame {} -- {}".format(event["commandId"], eName, frame, event["bytes"]))

        frameInfo = FrameInfo(canAutocancel, canIasa, chargeFrame, projectile, activeHitboxes, throw)
        frameData.append(frameInfo)

        if totalFrames:
            if totalFrames == frame:
                break
        else:
            if currentEvent >= len(events):
                break

        frame += 1

    return frameData

def getAutoCancelWindow(frameData):
    autoCancelBefore = 0
    for i, frame in enumerate(frameData):
        if frame.canAutocancel:
            autoCancelBefore = i + 1
        else:
            break

    autoCancelAfter = len(frameData) + 1
    for i in range(autoCancelBefore, len(frameData)):
        if frameData[i].canAutocancel:
            autoCancelAfter = i + 1
            break

    # autoCancelBefore is the last frame we can autocancel and autoCancelAfter is the first
    return autoCancelBefore + 1, autoCancelAfter - 1

def getIasa(frameData):
    for i, frame in enumerate(frameData):
        if frame.canIasa:
            return i + 1
    return None

def getChargeFrame(frameData):
    for i, frame in enumerate(frameData):
        if frame.chargeFrame:
            return i + 1
    return None

def getProjectileFrames(frameData):
    return [i+1 for i in range(len(frameData)) if frameData[i].projectile]

def expandSubroutines(events, subroutines, selfOffset=None, visited=None):
    if visited == None:
        visited = {}

    ret = []
    for event in events:
        if event.get("name") == "subroutine" or event.get("name") == "goto":
            offset = event["fields"]["location"]
            if offset in visited:
                # Recursion detected!
                # This usually happens with Attack100Loop, the rapid jap loop
                # In this case it's sensible to just pretend the attack ended
                return ret
            visited[offset] = True

            expanded = expandSubroutines(subroutines[str(offset)], subroutines, offset, visited)
            if expanded == None: # bubble up errors
                return None

            if expanded[-1].get("name") == "return":
                assert event.get("name") == "goto"
                expanded = expanded[:-1] # remove "return"

            if expanded[-1].get("name") == "exit":
                if event.get("name") == "subroutine":
                    # just remove "exit", put the rest in the stream
                    expanded = expanded[:-1]
                if event.get("name") == "goto":
                    # exit the whole script, not just return
                    # this branch will be entered in every "layer above"
                    ret.extend(expanded)
                    return ret

            ret.extend(expanded)
        else:
            ret.append(event)
    return ret

def getAttackSummary(data, subactionIndex, fullHitboxes):
    summary = odict()

    ftData = data["nodes"][0]["data"]

    subaction = ftData["subactions"][subactionIndex]
    print("Analyzing subaction {} - {} / {}".format(subactionIndex, subaction["name"], subaction["shortName"]))
    summary["subactionIndex"] = subactionIndex
    summary["subactionName"] = subaction["name"]

    if not "animationFile" in subaction:
        print("No animation! This character possibly does not have this attack.\n")
        return None
    animation = data["animationFiles"][subaction["animationFile"]]["nodes"][0]
    # The animation name is always the same as the subaction name
    # summary["animationName"] = animation["name"]

    totalFrames = animation["data"]["numFrames"]
    assert int(totalFrames) == totalFrames
    # for some reason the animation files contain numFrames that are 1 higher
    totalFrames = int(totalFrames) - 1
    summary["totalFrames"] = totalFrames

    airNormal = subactionIndex >= 0x44 and subactionIndex <= 0x48

    events = expandSubroutines(subaction["events"], ftData["subroutines"])
    if events == None:
        print("Recursion detected!\n")
        return None

    frameData = getFrameData(events, totalFrames, airNormal)

    chargeFrame = getChargeFrame(frameData)
    if chargeFrame:
        summary["chargeFrame"] = chargeFrame

    projectileFrames = getProjectileFrames(frameData)
    if len(projectileFrames) > 0:
        summary["projectiles"] = projectileFrames

    summary["iasa"] = getIasa(frameData)

    if airNormal:
        autoCancelBefore, autoCancelAfter = getAutoCancelWindow(frameData)
        summary["autoCancelBefore"] = autoCancelBefore
        summary["autoCancelAfter"] = autoCancelAfter

        landingLagAttribute = subactionIndex - 0x44 + 0x3a
        landingLag = int(ftData["attributes"][landingLagAttribute]["value"])
        summary["landingLag"] = landingLag
        summary["lcancelledLandingLag"] = math.floor(landingLag/2.0)

    # Throw
    for frame in frameData:
        if frame.throw:
            #assert not "throw" in summary
            if "throw" in summary:
                print("Multiple throw (0)! Only the first throw of the subaction is saved!")
            else:
                summary["throw"] = frame.throw.toJsonDict()

    # Hitframes
    hitFrames = []

    lastHitboxSetStart = 0
    lastHitboxSet = set()
    for i, frame in enumerate(frameData):
        hitboxSet = set()
        for hitbox in frame.hitboxes.values():
            hitboxSet.add(hitbox.guid)

        if lastHitboxSet != hitboxSet:
            if len(lastHitboxSet) > 0:
                if fullHitboxes:
                    hitboxes = [hitbox.toJsonDict() for hitbox in frameData[i-1].hitboxes.values()]
                else:
                    hitboxes = sorted({hitbox.groupId for hitbox in frameData[i-1].hitboxes.values()})
                hitFrames.append(odict([
                    ("start", lastHitboxSetStart),
                    ("end", i),
                    ("hitboxes", hitboxes),
                ]))
            lastHitboxSetStart = i+1

        lastHitboxSet = hitboxSet

    summary["hitFrames"] = hitFrames

    if not fullHitboxes:
        # a representative hitbox for each groupId
        summary["hitboxes"] = [hitbox.toJsonDict_onlyEffect() for hitbox in Hitbox.uniqueHitboxes]

    print()

    return summary

def getSpecialSubactions(data):
    ret = {}
    subactions = data["nodes"][0]["data"]["subactions"]
    charName = data["nodes"][0]["name"][len("ftData"):]
    for i in range(specialStartIndex, len(subactions)):
        if subactions[i]["shortName"].startswith("Special"):
            # we can't just use the actual names, since they are sometimes used multiple times
            name = hex(i)
            if charName in specialSubactions and i in specialSubactions[charName]:
                name = specialSubactions[charName][i]
            ret[name] = i
    return ret

def main():
    parser = argparse.ArgumentParser(description="Generate Frame data from JSON-dumped character .dat files")
    parser.add_argument("jsonfile", help="The JSON file with the dumped .dat character data.")
    parser.add_argument("outfile", help="The path to write the JSON output to.")
    parser.add_argument("--subactions", nargs="*", help="The subaction to analyze. Can be a subaction index or one of: " + ", ".join(attackMapping.keys()))
    parser.add_argument("--print", default=False, action="store_true", help="Print the contents of the JSON file nicely.")
    parser.add_argument("--fullhitboxes", default=False, action="store_true", help="Don't group the hitboxes by functional sameness, but rather include the all hitboxes fully (including boneId, size, transformations) in each hitframe.")
    args = parser.parse_args()

    with open(args.jsonfile) as inFile:
        data = json.load(inFile)

    defaultSubactions = attackMapping
    if args.subactions:
        subactions = {}

        for arg in args.subactions:
            if arg == "default" or arg == "defaults":
                subactions.update(defaultSubactions)
            elif arg == "special" or arg == "specials":
                subactions.update(getSpecialSubactions(data))
            else:
                parts = arg.split(":", 1)
                if len(parts) > 1:
                    name, index = parts[0], int(parts[1], 0)
                else:
                    try:
                        index = int(parts[0], 0)
                        name = index
                    except ValueError:
                        name = parts[0]
                        try:
                            index = attackMapping[name]
                        except KeyError:
                            quit("Unknown predefined subaction '{}'".format(name))
                subactions[name] = index
    else:
        subactions = defaultSubactions.copy()
        subactions.update(getSpecialSubactions(data))

    outJson = odict()
    for name in sorted(subactions, key=lambda x: subactions[x]):
        subactionIndex = subactions[name]
        summary = getAttackSummary(data, subactionIndex, args.fullhitboxes)
        outJson[name] = summary

        if args.print and summary:
            printAttackSummary(summary)

    with open(args.outfile, "w") as outFile:
        json.dump(outJson, outFile, indent=4)

if __name__ == "__main__":
    main()
