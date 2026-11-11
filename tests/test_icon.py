from PIL import Image

from pomodoro.assets import ICON_ICO_PATH, ICON_PNG_PATH
from pomodoro.tray import ICON_SIZE, make_icon


def test_icon_files_exist():
    assert ICON_ICO_PATH.exists()
    assert ICON_PNG_PATH.exists()


def test_ico_contains_multiple_sizes():
    with Image.open(ICON_ICO_PATH) as im:
        sizes = set(im.info.get("sizes", set()))
    assert (16, 16) in sizes and (256, 256) in sizes


def test_tray_icon_has_expected_size_and_state():
    idle = make_icon(running=False)
    running = make_icon(running=True)
    assert idle.size == (ICON_SIZE, ICON_SIZE) == running.size
    assert idle.tobytes() != running.tobytes()
