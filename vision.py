from __future__ import annotations
import math

try:
    from .capture import GameImage
except ImportError:
    from capture import GameImage  # type: ignore[no-redef]

def get_skill_button_buff_pos(width: int, height: int, button_id: int, percent: float) -> list[int]:
    xs = [1288, 1377, 1465, 1554, 1647, 1734]
    bar_width = 63
    y = 1328 * height / 1440.0
    x = width / 2.0 - (3440 / 2.0 - xs[button_id - 1] - percent * bar_width) * height / 1440.0
    return [round(x), round(y)]


def get_inventory_space_xy(width: int, height: int, slot_id: int, zone: str) -> list[int]:
    space_size_inner_w = 64
    space_size_inner_h = 63
    bag_x = [2753, 2820, 2887, 2954, 3021, 3089, 3156, 3223, 3290, 3357]
    bag_y = [747, 813, 880, 946, 1013, 1079]
    kanai_x = [242, 318, 394]
    kanai_y = [503, 579, 655]
    if zone == "bag":
        column = 10 if slot_id % 10 == 0 else slot_id % 10
        row = math.floor((slot_id - 1) / 10) + 1
        return [
            round(width - ((3440 - bag_x[column - 1] - space_size_inner_w / 2) * height / 1440.0)),
            round((bag_y[row - 1] + space_size_inner_h / 2) * height / 1440.0),
            round(width - ((3440 - bag_x[column - 1]) * height / 1440.0)),
            round(bag_y[row - 1] * height / 1440.0),
        ]
    column = 3 if slot_id % 3 == 0 else slot_id % 3
    row = math.floor((slot_id - 1) / 3) + 1
    return [
        round((kanai_x[column - 1] + space_size_inner_w / 2) * height / 1440.0),
        round((kanai_y[row - 1] + space_size_inner_h / 2) * height / 1440.0),
        round(kanai_x[column - 1] * height / 1440.0),
        round(kanai_y[row - 1] * height / 1440.0),
    ]


def get_kanai_cube_button_pos(height: int) -> list[list[int]]:
    return [
        [round(320 * height / 1440.0), round(1105 * height / 1440.0)],
        [round(955 * height / 1440.0), round(1115 * height / 1440.0)],
        [round(777 * height / 1440.0), round(1117 * height / 1440.0)],
        [round(1135 * height / 1440.0), round(1117 * height / 1440.0)],
    ]


def get_salvage_icon_xy(height: int, mode: str) -> list[list[int]]:
    if mode == "center":
        return [
            [round(221 * height / 1440.0), round(388 * height / 1440.0)],
            [round(335 * height / 1440.0), round(388 * height / 1440.0)],
            [round(424 * height / 1440.0), round(388 * height / 1440.0)],
            [round(514 * height / 1440.0), round(388 * height / 1440.0)],
        ]
    return [
        [round(203 * height / 1440.0), round(337 * height / 1440.0)],
        [round(335 * height / 1440.0), round(371 * height / 1440.0)],
        [round(424 * height / 1440.0), round(371 * height / 1440.0)],
        [round(514 * height / 1440.0), round(371 * height / 1440.0)],
    ]


def is_dialog_box_on_screen(image: GameImage, width: int, height: int) -> bool:
    point1 = [width / 2 - (3440 / 2 - 1655) * height / 1440.0, 500 * height / 1440.0]
    point2 = [width / 2 + (3440 / 2 - 1800) * height / 1440.0, 500 * height / 1440.0]
    c1 = image.get_pixel_rgb(point1)
    c2 = image.get_pixel_rgb(point2)
    return bool(
        c1[0] > c1[1] > c1[2]
        and c1[2] < 5
        and c1[1] < 15
        and c1[0] > 25
        and c2[0] > c2[1] > c2[2]
        and c2[2] < 5
        and c2[1] < 15
        and c2[0] > 25
    )


def is_salvage_page_open(image: GameImage, width: int, height: int):
    c1 = image.get_pixel_rgb([round(339 * height / 1440.0), round(80 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(351 * height / 1440.0), round(107 * height / 1440.0)])
    c3 = image.get_pixel_rgb([round(388 * height / 1440.0), round(86 * height / 1440.0)])
    c4 = image.get_pixel_rgb([round(673 * height / 1440.0), round(1040 * height / 1440.0)])
    if not (
        c1[2] > c1[1] > c1[0]
        and c1[2] > 170
        and c1[2] - c1[0] > 80
        and c3[2] > c3[1] > c3[0]
        and c3[2] > 110
        and c2[0] + c2[1] > 350
        and c4[0] > 50
        and c4[1] < 15
        and c4[2] < 15
    ):
        return [0]
    edges = get_salvage_icon_xy(height, "edge")
    c_leg = image.get_pixel_rgb(edges[0])
    c_white = image.get_pixel_rgb(edges[1])
    c_blue = image.get_pixel_rgb(edges[2])
    c_rare = image.get_pixel_rgb(edges[3])
    if c_blue[2] > c_blue[1] > c_blue[0] and c_rare[2] < 20 and c_rare[0] > c_rare[1] > c_rare[2]:
        return [2, c_leg, c_white, c_blue, c_rare]
    return [1]


def salvage_mode_is_armed(salvage_state) -> bool:
    return bool(
        len(salvage_state) > 1
        and len(salvage_state[1]) >= 3
        and salvage_state[1][2] < 10
        and salvage_state[1][0] + salvage_state[1][1] > 400
    )


def salvage_bulk_buttons_from_state(salvage_state) -> list[int]:
    if len(salvage_state) < 5:
        return []
    buttons: list[int] = []
    if salvage_state[4][0] > 50:
        buttons.append(3)
    if salvage_state[3][2] > 65:
        buttons.append(2)
    if salvage_state[2][0] > 65:
        buttons.append(1)
    return buttons


def _is_kanai_cube_shell_visible(image: GameImage, height: int) -> bool:
    c1 = image.get_pixel_rgb([round(353 * height / 1440.0), round(85 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(278 * height / 1440.0), round(147 * height / 1440.0)])
    c3 = image.get_pixel_rgb([round(330 * height / 1440.0), round(140 * height / 1440.0)])
    return bool(
        c1[0] < 50
        and c1[1] < 40
        and c1[2] < 35
        and c2[0] > 100
        and c2[1] < 30
        and c2[2] < 30
        and abs(c3[2] - c3[1]) <= 8
        and c3[0] <= 55
        and c3[0] < c3[1]
        and c3[0] < c3[2]
    )


def _is_kanai_reforge_page(image: GameImage, height: int) -> bool:
    cc1 = image.get_pixel_rgb([round(788 * height / 1440.0), round(428 * height / 1440.0)])
    cc2 = image.get_pixel_rgb([round(810 * height / 1440.0), round(429 * height / 1440.0)])
    return bool(cc1[2] > 230 and cc2[2] > 230 and cc1[2] > cc1[1] > cc1[0] and cc2[2] > cc2[1] > cc2[0])


def _is_kanai_upgrade_page(image: GameImage, height: int) -> bool:
    for offset in (0, -22):
        cc1 = image.get_pixel_rgb([round(799 * height / 1440.0), round((406 + offset) * height / 1440.0)])
        cc2 = image.get_pixel_rgb([round(795 * height / 1440.0), round((592 + offset) * height / 1440.0)])
        if cc1[0] + cc1[1] + cc1[2] > 550 and cc1[0] > cc1[2] and cc2[0] + cc2[1] > 400 and cc2[0] > cc2[2]:
            return True
    return False


def _is_kanai_convert_page(image: GameImage, height: int) -> bool:
    for offset in (0, -43):
        cc3 = image.get_pixel_rgb([round(799 * height / 1440.0), round((365 + offset) * height / 1440.0)])
        if cc3[0] + cc3[1] + cc3[2] > 600 and cc3[0] > cc3[1] > cc3[2] and 110 < cc3[2] < 200:
            return True
    return False


def is_kanai_cube_open(image: GameImage, width: int, height: int, title: str):
    if _is_kanai_reforge_page(image, height):
        return 2
    if _is_kanai_upgrade_page(image, height):
        return 3
    if _is_kanai_convert_page(image, height):
        return 4
    if _is_kanai_cube_shell_visible(image, height):
        return 1
    return 0


def is_gamble_open(image: GameImage, height: int) -> bool:
    c1 = image.get_pixel_rgb([round(320 * height / 1440.0), round(96 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(351 * height / 1440.0), round(100 * height / 1440.0)])
    c4 = image.get_pixel_rgb([round(194 * height / 1440.0), round(67 * height / 1440.0)])
    c5 = image.get_pixel_rgb([round(147 * height / 1440.0), round(94 * height / 1440.0)])
    return bool(c1[2] > c1[0] > c1[1] and c1[2] > 130 and c2[0] + c2[1] > 330 and sum(c4) + sum(c5) < 10)


def is_inventory_open(image: GameImage, width: int, height: int) -> bool:
    c1 = image.get_pixel_rgb([round(width - (3440 - 3086) * height / 1440.0), round(108 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(width - (3440 - 3010) * height / 1440.0), round(147 * height / 1440.0)])
    c3 = image.get_pixel_rgb([round(width - (3440 - 3425) * height / 1440.0), round(142 * height / 1440.0)])
    c4 = image.get_pixel_rgb([round(width - (3440 - 3117) * height / 1440.0), round(84 * height / 1440.0)])
    return bool(
        c1[0] + c1[1] > 240
        and c2[0] > 115
        and c2[1] < 30
        and c2[2] < 30
        and abs(c3[0] - c3[1]) <= 10
        and c3[2] < 40
        and c4[2] > c4[1] + 60
        and c4[1] > c4[0]
    )


def is_stash_open(image: GameImage, height: int) -> bool:
    c1 = image.get_pixel_rgb([round(282 * height / 1440.0), round(147 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(382 * height / 1440.0), round(77 * height / 1440.0)])
    c3 = image.get_pixel_rgb([round(299 * height / 1440.0), round(82 * height / 1440.0)])
    return bool(
        c1[0] > 100
        and c1[0] > c1[1] + 80
        and abs(c1[1] - c1[2]) < 10
        and c2[1] > c2[2] > c2[0]
        and c2[1] - c2[0] > 80
        and c3[0] > c3[1] > c3[2]
        and c3[2] < 40
    )


def is_inventory_space_empty(image: GameImage, width: int, height: int, slot_id: int, zone: str, checkpoints=None) -> bool:
    space_w = 64
    space_h = 63
    x_center, y_center, x0, y0 = get_inventory_space_xy(width, height, slot_id, zone)
    if not checkpoints:
        c = image.get_pixels_rgb(
            round(x0 + 0.2 * space_w),
            round(y0 + 0.2 * space_h),
            round(0.6 * space_w),
            round(0.6 * space_h),
            "max",
        )
        return bool(c[0] <= 50 and c[1] <= 50 and c[2] <= 50)
    for check in checkpoints:
        xy = [round(x0 + space_w * check[0] * height / 1440.0), round(y0 + space_h * check[1] * height / 1440.0)]
        c = image.get_pixel_rgb(xy)
        if not (c[0] < 22 and c[1] < 20 and c[2] < 15 and c[0] > c[2] and c[1] > c[2]):
            return False
    return True


def scan_inventory_space(image: GameImage, width: int, height: int, safezone: set[int]):
    helper_bag_zone = [-1] * 61
    inventory_colors: dict[int, list[int]] = {}
    raw_values: dict[int, int] = {}
    points = [(0.65625, 0.71429), (0.375, 0.36508), (0.725, 0.251)]
    for index in range(1, 61):
        x_center, y_center, x0, y0 = get_inventory_space_xy(width, height, index, "bag")
        inventory_colors[index] = image.get_pixel_rgb(
            [round(x0 + 64 * 0.08 * height / 1440.0), round(y0 + 63 * 0.7 * height / 1440.0)]
        )
        slot_value = 1
        for px, py in points:
            c = image.get_pixel_rgb([round(x0 + 64 * px * height / 1440.0), round(y0 + 63 * py * height / 1440.0)])
            if not (c[0] < 22 and c[1] < 20 and c[2] < 15 and c[0] > c[2] and c[1] > c[2]):
                slot_value = 10
                break
        raw_values[index] = slot_value
        helper_bag_zone[index] = 0 if index in safezone else slot_value

    # Protect slots directly below/right of a safezone slot that contains an item.
    # A 2-tall item anchored in a safezone slot has its lower half visible in the
    # slot below (+10), which is not in safezone and would otherwise be processed.
    for safe_slot in safezone:
        if raw_values.get(safe_slot) != 10:
            continue
        # Vertical overflow: slot directly below (same column, next row)
        below = safe_slot + 10
        if below <= 60 and below not in safezone and helper_bag_zone[below] == 10:
            helper_bag_zone[below] = 0
        # Horizontal overflow: slot immediately to the right (same row only)
        right = safe_slot + 1
        if (right <= 60 and right not in safezone
                and (safe_slot - 1) // 10 == (right - 1) // 10
                and helper_bag_zone[right] == 10):
            helper_bag_zone[right] = 0

    return helper_bag_zone, inventory_colors


