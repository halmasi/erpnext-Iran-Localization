"""Refresh once per Desk load, including cached boots; no per-control requests."""

from iran_localization.modules.core.settings import is_enabled


def extend_bootinfo(bootinfo):
	bootinfo.iran_localization = {"enable_persian_calendar": is_enabled("enable_persian_calendar")}
