from pomodoro.assets import ICON_ICO_PATH
from pomodoro.ui import icon as icon_mod


class FakeWindow:
    def __init__(self):
        self.icons = []
        self.scheduled = []

    def iconbitmap(self, path):
        self.icons.append(path)

    def after(self, ms, fn):
        self.scheduled.append((ms, fn))


def test_apply_sets_icon_now_and_reapplies_later():
    win = FakeWindow()
    icon_mod.apply_window_icon(win)
    assert ICON_ICO_PATH.exists()
    assert win.icons == [str(ICON_ICO_PATH)]
    assert len(win.scheduled) == 1
    _, reapply = win.scheduled[0]
    reapply()
    assert win.icons == [str(ICON_ICO_PATH)] * 2


def test_missing_after_does_not_raise():
    class NoAfter:
        def iconbitmap(self, path):
            pass

    icon_mod.apply_window_icon(NoAfter())


def test_iconbitmap_failure_is_not_fatal():
    class Broken:
        def iconbitmap(self, path):
            raise RuntimeError("sem suporte a .ico")

        def after(self, ms, fn):
            pass

    icon_mod.apply_window_icon(Broken())
