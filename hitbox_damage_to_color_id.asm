# heavily based on:
# https://smashboards.com/threads/custom-hitbox-id-colors.427023/
# https://smashboards.com/threads/hitbox-color-darkens-based-on-damage.454256/
# at beginning of CollisionBubbles_HitboxDisplay
# r25 = hitbox ID (0-indexed)

lwz r0, 0(r3) # default code line, load hitbox active bool

lwz r25, 0x8(r3) # get hitbox damage

cmpwi r25, 0
beq RED

cmpwi r25, 1
beq GREEN

cmpwi r25, 2
beq YELLOW

cmpwi r25, 3
beq BLUE

cmpwi r25, 4
beq PURPLE

cmpwi r25, 5
beq CYAN

# default color
b GREY

RED:
lis r5, 0xe619
ori r5, r5, 0x4b80
b COLOR_FINISH

GREEN:
lis r5, 0x3cb4
ori r5, r5, 0x4b80
b COLOR_FINISH

YELLOW:
lis r5, 0xffe1
ori r5, r5, 0x1980
b COLOR_FINISH

BLUE:
lis r5, 0x0082
ori r5, r5, 0xc880
b COLOR_FINISH

ORANGE:
lis r5, 0xf582
ori r5, r5, 0x3180
b COLOR_FINISH

PURPLE:
lis r5, 0x911e
ori r5, r5, 0xb480
b COLOR_FINISH

CYAN:
lis r5, 0x46f0
ori r5, r5, 0xf080
b COLOR_FINISH

GREY:
lis r5, 0x8080
ori r5, r5, 0x8080
b COLOR_FINISH

COLOR_FINISH:
stw r5,-0x8000(r13) # store color @804d36a0 = hitbox RGBA value

