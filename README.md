# meleeFrameDataExtractor
meleeFrameDataExtractor is a program that utilizes [meleeDat2Json](https://github.com/pfirsich/meleeDat2Json), which dumps Super Smash Bros. Melee character files to JSON. The subactions/scrips that belong to character attack states are then parsed by this program to produce frame data, which previously had to be determined manually (by community assets such as [superdoodleman](http://www.angelfire.com/games5/superdoodleman/frames.html)). This enables us to go into significantly more detail (i.e. include every single hitbox of a move) and do postprocessing on the data as well. The framedata is generated as JSON for easier inclusion in other projects (like websites, etc.), but an additional script is provided to produce text output from those JSON files, that very similar to the frame data on superdoodleman's website.

## Usage
To use meleeFrameDataExtractor, you need Python 3, then navigate to the root of the repository and call:
```console
python generateFrameData.py --help
```
To see help on the arguments. The default subactions included in the framedata JSON file only include jabs, tilts, grabs, throws, etc., but not specials! If you know the subaction ids you can pass them to the program, but they are not included automatically.

By default the "functionally equivalent" hitboxes are grouped and given a name. Functional equivalency is determined by having the same post-hit effect and hitting the same targets. If you want to see all hitboxes fully instead, without them being pre-grouped by the program, pass `--fullhitboxes`.

If you want to print the framedata to console (in a format you are probably more familiar with), just call:
```
python prettyPrint.py <Character>.framedata.json <movename>
```

## Framedata Dumps
Most people don't have to generate the framedata dumps themselves and can just use the ones I prepared:
* [framedata-json](http://melee.theshoemaker.de/?dir=framedata-json)
* [framedata-json-fullhitboxes](http://melee.theshoemaker.de/?dir=framedata-json-fullhitboxes)

## [melee-framedata](http://melee-framedata.theshoemaker.de/)
The data generated with this tool is included in a website made by me that presents it in a more accessible manner and uses the hitbox grouping information to produce pages and gfycats like here: [Samus - Dash Attack](http://melee-framedata.theshoemaker.de/samus/dashattack.html) or [Samus - Neutral Air](http://melee-framedata.theshoemaker.de/samus/nair.html)

## ToDo
* Add special subactions for each character
* Process events `0x68`, `0x6C` and `0x70` that modify bone/body collision state and include invincibility data into framedata JSON files.
* Process events `0x74` and `0x78` that modify jab follow up state and include data about when jab followups are possible into framedata JSON files.
* Process the `0xCC` (self damage) event and include that data in the framedata file.
* Find out if it is possible to determine which projectile is shot by the `0x60` event. It seems the event is alway `60 00 00 00` and some characters even use other events to shoot projectiles.

## Commands to figure out if they are relevant
* `0x7C` ("model_state"?)
* `0x8C` ("held_item_invisibility"?)
* `0xC8` ("enable_ragdoll_physics"?)
* `0x64`
