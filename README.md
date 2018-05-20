# ToDo
* Process events `0x68`, `0x6C` and `0x70` that modify bone/body collision state and include invincibility data into framedata JSON files.
* Process events `0x74` and `0x78` that modify jab follow up state and include data about when jab followups are possible into framedata JSON files.
* Donkey Kong only has a throw command of type 1 for ThrowF, because he keeps carrying the opponent. Currently this just ressults in an assertion failure. Somehow handle this properly.
* Process `0x60` event, which shoots a projectile (e.g. Fox/Falco ThrowHi, ThrowLw) and include that data in the framedata file.
* Process the `0xCC` (self damage) event and include that data in the framedata file.

## Commands to figure out if they are relevant
* `0x7C` ("model_state"?)
* `0x8C` ("held_item_invisibility"?)
* `0xC8` ("enable_ragdoll_physics"?)
* `0x64`
