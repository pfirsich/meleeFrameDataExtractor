import os
import json
import argparse
import webbrowser as wb

def getFrameGraph(summary):
    frameGraph = []
    lastHitFrame = None
    for frame in range(1, summary["totalFrames"] + 1):
        autoCancel = False
        if "landingLag" in summary:
            autoCancel = frame < summary["autoCancelBefore"]
            autoCancel = autoCancel or frame > summary["autoCancelAfter"]

        iasa = frame >= (summary["iasa"] or summary["totalFrames"] + 1)

        hitFrame = None
        for hf in summary["hitFrames"]:
            if frame >= hf["start"] and frame <= hf["end"]:
                hitFrame = hf

        h = 0
        if hitFrame:
            h = 1
            if lastHitFrame and lastHitFrame != hitFrame:
                h = 2
        a = int(autoCancel)
        i = int(iasa)
        frameGraph.append("a{}i{} h{}".format(a, i, h))

        lastHitFrame = hitFrame

    return frameGraph


def main():
    parser = argparse.ArgumentParser(description="Generate frame graph from JSON framedata files.")
    parser.add_argument("jsonfile", help="The JSON file with the framedata generated by generateFrameData.py")
    parser.add_argument("subaction", help="The subaction/move to generate a frame graph for. Must be present in the JSON file.")
    parser.add_argument("outfile", nargs="?", default="frameGraph.html", help="The output HTML file.")
    parser.add_argument("--open", default=False, action="store_true", help="Open the frame graph in the browser after creation.")
    args = parser.parse_args()

    with open(args.jsonfile) as inFile:
        frameData = json.load(inFile)

    if args.subaction not in frameData:
        quit("'{}' does not exist in '{}'".format(args.subaction, args.jsonfile))

    # Save Framegraph to HTML
    frameGraph = getFrameGraph(frameData[args.subaction])
    print("Writing to '{}'..".format(args.outfile))
    with open(args.outfile, "w") as frameGraphFile:
        cols = "\n".join('    <td class="{}"></td>'.format(frame) for frame in frameGraph)
        frameGraphFile.write("""<html>
        <head>
            <link rel="stylesheet" type="text/css" href="frameGraph.css">
        </head>
        <body>
            <table class="framegraph" cellspacing="0" cellpadding="0"><tbody><tr>
            {}
            </tr></tbody></table>
        </body>
        </html>
        """.format(cols))

    if args.open:
        wb.open("file:///" + os.path.abspath(args.outfile))

if __name__ == "__main__":
    main()