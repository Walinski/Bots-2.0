import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class SafeMessages:
    OK = 22
    HI_THERE = 101
    HELLO = 1
    HOW_U_DOING = 151
    SEE_U_LATER = 212
    FOLLOW_ME = 310
    U_ARE_SILLY = 354
    PARTY_AT_MY_IGLOO = 712
    WHERE = 410
    GO_AWAY = 802
    
@dataclass(frozen=True)
class ItemType:
    COLOR = 1
    HEAD = 2
    FACE = 3
    NECK = 4
    BODY = 5
    HAND = 6
    FEET = 7
    FLAG = 8
    PHOTO = 9
    AWARD = 10
    
@dataclass
class RoomSpot:
    position: Tuple[float, float]
    frame: int
    priority: int
    clothes: dict[int, int] | None = None
    
class RoomSpotsController:
    def __init__(self, spots: list['RoomSpot']) -> None:
        self.spots: list[list['RoomSpot']] = [list(x) for _, x in itertools.groupby(spots, key=lambda x: x.priority)]
        self.total = self.len_spots()
        
    def len_spots(self) -> int:
        return len([y for x in self.spots for y in x])
        
ROOM_AREAS = defaultdict(lambda: [(190, 300), (530, 300), (530, 450), (190, 450)]) # defaults if you try to access a room ID that doesn�t have a specific set of coordinates
ROOM_AREAS[100] = [(135, 340), (165, 280), (306, 203), (457, 210), (573, 283), (635, 360), (605, 405), (180, 410)]
ROOM_AREAS[110] = [(501.0, 258.0), (445.25, 184.55), (202.15, 188.45), (162.6, 201.4), (88.85, 257.8), (0.0, 370.5), (0.0, 480.0), (668.0, 481.0)]
ROOM_AREAS[111] = [(311.0, 190.0), (235.0, 217.0), (129.9, 307.25), (59.0, 433.0), (687.0, 433.0), (568.95, 254.0), (504.0, 182.0), (459.95, 174.0), (352.0, 174.0)]
ROOM_AREAS[120] = [(660.0, 428.0), (519.75, 213.65), (421.7, 126.0), (247.1, 126.0), (186.85, 177.1), (121.0, 236.0), (0.0, 430.0)]
ROOM_AREAS[121] = [(616.0, 266.0), (190.0, 217.0), (134.0, 238.0), (0.0, 359.05), (0.0, 450.0), (760.0, 450.0), (760.0, 329.15), (703.95, 280.0)]
ROOM_AREAS[130] = [(353.0, 219.0), (0.0, 434.0), (0.0, 450.0), (760.0, 450.0), (605.95, 290.0)]
ROOM_AREAS[300] = [(579.65, 450.0), (676.5, 411.5), (729.15, 342.75), (694.2, 276.8), (634.5, 254.5), (536.2, 225.9), (514.2, 224.5), (328.5, 224.5), (148.5, 265.5), (94.5, 380.5), (146.0, 450.0)]
ROOM_AREAS[310] = [(760.0, 292.05), (659.5, 232.5), (483.5, 181.5), (327.0, 217.0), (0.0, 348.8), (0.0, 450.0), (760.0, 450.0), (760.0, 292.05)]
ROOM_AREAS[320] = [(477.75, 289.95), (453.55, 286.0), (124.9, 286.0), (0.0, 354.55), (0.0, 450.0), (760.0, 450.0), (760.0, 348.5), (536.9, 313.7), (512.75, 309.4), (494.2, 299.55)]
ROOM_AREAS[321] = [(510.95, 403.0), (629.2, 403.0), (554.05, 313.0), (449.95, 313.0), (432.6, 289.0), (347.0, 289.0), (329.65, 313.0), (256.0, 313.0), (184.0, 330.0), (86.9, 330.0), (7.0, 379.65), (7.0, 413.0), (162.5, 413.0), (197.0, 403.0), (274.0, 403.0)]
ROOM_AREAS[330] = [(119.5, 450.0), (760.0, 450.0), (760.0, 221.75), (680.5, 174.5), (567.35, 175.05), (487.5, 208.5), (352.5, 208.5), (312.5, 221.5), (164.5, 208.5), (149.5, 208.5), (119.5, 221.5)]
ROOM_AREAS[200] = [(671.0, 235.0), (664.0, 230.0), (587.0, 239.0), (557.0, 233.6), (462.95, 197.8), (214.0, 200.0), (177.0, 325.0), (112.0, 390.0), (112.0, 450.0), (689.95, 450.0), (689.95, 341.4)]
ROOM_AREAS[210] = [(353.0, 219.0), (0.0, 434.0), (0.0, 450.0), (760.0, 450.0), (605.95, 290.0)]
ROOM_AREAS[220] = [(623.45, 223.05), (406.1, 223.05), (250.1, 213.05), (228.05, 213.05), (0.0, 347.9), (0.0, 450.0), (760.0, 450.0), (760.0, 342.65)]
ROOM_AREAS[221] = [(628.95, 363.0), (652.95, 314.0), (545.95, 271.0), (318.95, 271.0), (136.95, 295.05), (137.6, 343.35), (152.3, 480.05), (628.95, 480.05)]
ROOM_AREAS[230] = [(595.5, 224.5), (498.5, 126.5), (371.5, 117.5), (206.5, 157.5), (95.75, 270.05), (96.5, 270.5), (206.5, 344.5), (367.5, 374.5), (496.5, 365.5), (585.5, 313.5), (596.5, 224.5), (595.5, 224.5)]
ROOM_AREAS[801] = [(760.0, 203.55), (675.3, 172.5), (538.3, 158.85), (320.0, 169.1), (207.3, 200.9), (121.0, 204.0), (115.0, 255.0), (115.0, 301.0), (76.0, 337.0), (63.0, 392.0), (0.0, 432.8), (760.0, 432.8)]
ROOM_AREAS[802] = [(417.95, 148.0), (338.95, 86.0), (175.0, 165.0), (111.0, 234.0), (114.0, 325.0), (222.0, 391.0), (377.0, 418.0), (645.95, 362.0), (681.0, 265.0), (618.95, 170.0)]
ROOM_AREAS[804] = [(760.0, 392.05), (489.0, 287.75), (376.85, 287.75), (260.5, 306.65), (200.75, 360.6), (141.0, 450.0), (760.0, 450.0)]
ROOM_AREAS[800] = [(570.5, 89.5), (262.5, 74.5), (172.9, 129.25), (33.5, 265.5), (79.5, 401.5), (179.5, 427.5), (286.0, 388.0), (317.5, 416.5), (393.5, 416.5), (460.5, 443.5), (526.5, 419.5), (617.5, 419.5), (677.1, 317.25), (676.55, 309.6), (702.5, 240.5), (702.5, 145.5), (601.95, 121.35)]
ROOM_AREAS[400] = [(648.85, 334.25), (666.55, 303.35), (642.0, 223.0), (616.85, 208.4), (551.2, 194.15), (521.65, 164.7), (507.35, 148.4), (497.75, 140.05), (366.3, 150.5), (250.7, 195.25), (164.5, 203.9), (76.9, 191.45), (41.55, 225.4), (23.65, 286.35), (39.25, 302.6), (153.4, 342.4), (186.8, 353.9), (218.9, 366.0), (276.9, 401.0), (326.95, 428.2), (419.9, 439.3), (550.0, 401.0)]
ROOM_AREAS[410] = [(0.0, 450.0), (760.0, 450.0), (760.0, 316.8), (646.95, 326.9), (585.55, 307.95), (556.35, 305.3), (533.9, 299.5), (503.0, 282.9), (412.6, 248.15), (338.4, 227.2), (181.55, 243.35), (113.15, 229.1), (71.5, 224.45), (0.0, 260.0)]
ROOM_AREAS[809] = [(631.95, 155.15), (424.95, 131.0), (359.3, 134.25), (237.4, 142.9), (62.8, 163.95), (53.2, 206.0), (58.1, 267.55), (65.2, 326.25), (121.55, 386.4), (311.85, 422.6), (494.4, 480.0), (635.85, 480.0), (690.75, 395.1), (690.75, 178.25)]
ROOM_AREAS[805] = [(515.2, 172.6), (487.55, 168.95), (374.6, 139.95), (297.35, 107.15), (256.8, 86.85), (219.15, 86.85), (174.75, 107.2), (122.6, 153.5), (104.25, 185.35), (47.3, 260.65), (37.65, 300.25), (124.55, 337.9), (294.45, 368.8), (481.75, 351.4), (610.15, 302.15), (642.65, 265.55), (701.0, 209.85), (515.2, 172.6)]
ROOM_AREAS[810] = [(723.8, 222.4), (644.25, 185.4), (576.2, 176.9), (556.85, 158.2), (520.95, 147.0), (420.95, 150.0), (376.2, 144.75), (340.8, 133.4), (307.5, 133.4), (273.0, 164.0), (223.0, 192.0), (212.0, 216.0), (112.0, 226.15), (60.3, 311.95), (112.0, 384.15), (143.3, 406.5), (245.0, 454.95), (255.45, 480.0), (639.2, 480.0), (760.0, 397.8), (760.0, 290.7)]
ROOM_AREAS[806] = [(690.7, 288.35), (591.35, 270.3), (428.25, 256.05), (275.4, 262.4), (221.0, 237.7), (220.75, 237.55), (207.1, 234.45), (184.95, 236.8), (177.15, 241.1), (172.65, 250.2), (166.0, 259.05), (154.2, 267.05), (139.2, 274.55), (121.9, 278.55), (112.5, 281.85), (110.4, 282.15), (36.2, 343.95), (76.95, 404.0), (161.15, 450.0), (710.4, 450.0), (691.65, 423.2)]
ROOM_AREAS[808] = [(760.0, 280.0), (671.95, 242.0), (581.95, 185.0), (471.95, 148.0), (253.95, 174.0), (0.0, 290.0), (0.0, 420.95), (167.95, 450.0), (760.0, 450.0)]
ROOM_AREAS[807] = [(475.85, 271.1), (331.15, 226.55), (113.3, 187.95), (99.2, 306.2), (99.2, 306.2), (140.1, 355.75), (164.0, 400.0), (164.0, 480.0), (464.9, 480.0), (628.7, 425.35), (663.7, 393.5), (760.0, 357.55), (760.0, 272.0)]
ROOM_AREAS[420] = [(417.95, 357.0), (545.95, 353.0), (710.95, 205.0), (468.95, 175.0), (111.0, 175.0), (49.0, 286.0), (108.0, 324.0), (227.95, 357.0)]
ROOM_AREAS[423] = [(485.25, 208.45), (437.8, 204.75), (335.35, 205.35), (268.65, 275.65), (219.35, 300.0), (220.15, 358.7), (338.2, 383.15), (432.85, 382.4), (486.1, 373.45), (576.75, 340.0), (584.95, 332.55), (598.5, 313.85), (602.45, 289.5), (599.7, 260.5), (590.15, 222.9), (581.8, 208.85), (545.25, 199.8), (502.7, 210.9)]
ROOM_AREAS[421] = [(671.95, 285.0), (628.95, 235.0), (143.1, 235.0), (113.0, 315.0), (47.35, 360.3), (47.35, 450.0), (671.95, 450.0)]
ROOM_AREAS[422] = [(155.0, 310.0), (55.0, 349.0), (0.0, 408.85), (0.0, 480.0), (741.95, 480.0), (706.95, 337.0), (590.95, 310.0), (477.7, 284.65), (281.0, 275.0)]

SAFE_MESSAGES = SafeMessages()
ITEM_TYPE = ItemType()

ROOM_SPOTS = defaultdict(lambda: RoomSpotsController([]))
ROOM_SPOTS[110] = RoomSpotsController([RoomSpot(position=(255, 188), frame=17, priority=1), RoomSpot(position=(124, 241), frame=24, priority=1), RoomSpot(position=(274, 250), frame=26, priority=2, clothes={ITEM_TYPE.BODY: 262}), RoomSpot(position=(224, 291), frame=26, priority=3, clothes={ITEM_TYPE.BODY: 262}), RoomSpot(position=(216, 190), frame=17, priority=3), RoomSpot(position=(294, 186), frame=17, priority=3), RoomSpot(position=(103, 262), frame=24, priority=3)])
ROOM_SPOTS[330] = RoomSpotsController([RoomSpot(position=(346, 368), frame=24, priority=1), RoomSpot(position=(383, 331), frame=26, priority=2, clothes={ITEM_TYPE.BODY: 263, ITEM_TYPE.HEAD: 424}), RoomSpot(position=(420, 365), frame=18, priority=2), RoomSpot(position=(207, 309), frame=24, priority=2), RoomSpot(position=(247, 283), frame=26, priority=3, clothes={ITEM_TYPE.BODY: 263, ITEM_TYPE.HEAD: 424}), RoomSpot(position=(285, 309), frame=18, priority=3), RoomSpot(position=(493, 351), frame=24, priority=3), RoomSpot(position=(574, 349), frame=18, priority=3), RoomSpot(position=(529, 316), frame=26, priority=4, clothes={ITEM_TYPE.BODY: 263, ITEM_TYPE.HEAD: 424}), RoomSpot(position=(551, 212), frame=26, priority=4, clothes={ITEM_TYPE.HAND: 343})])
ROOM_SPOTS[410] = RoomSpotsController([RoomSpot(position=(87, 225), frame=26, priority=1, clothes={ITEM_TYPE.HAND: 340}), RoomSpot(position=(132, 313), frame=26, priority=1, clothes={ITEM_TYPE.HAND: 233}), RoomSpot(position=(48, 326), frame=26, priority=1, clothes={ITEM_TYPE.HAND: 234}), RoomSpot(position=(104, 354), frame=26, priority=1, clothes={ITEM_TYPE.BODY: 293}), RoomSpot(position=(185, 389), frame=22, priority=1), RoomSpot(position=(367, 324), frame=19, priority=2), RoomSpot(position=(185, 389), frame=22, priority=2), RoomSpot(position=(462, 335), frame=22, priority=2)])
ROOM_SPOTS[810] = RoomSpotsController([RoomSpot(position=(296, 265), frame=18, priority=1), RoomSpot(position=(260, 252), frame=18, priority=1), RoomSpot(position=(448, 391), frame=26, priority=1, clothes={ITEM_TYPE.HAND: 325}), RoomSpot(position=(563, 380), frame=26, priority=1, clothes={ITEM_TYPE.HAND: 325}), RoomSpot(position=(337, 141), frame=17, priority=2), RoomSpot(position=(136, 265), frame=24, priority=2), RoomSpot(position=(137, 355), frame=22, priority=2)])
