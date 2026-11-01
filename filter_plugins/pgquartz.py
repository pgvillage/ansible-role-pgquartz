"""Filters for the pgvillage.pgquartz role."""

from ansible.errors import AnsibleFilterError

DOW_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# First value of a field, used as start for a step on '*' (cron '*/15' is systemd '0/15')
FIELD_START = {"minute": 0, "hour": 0, "dom": 1, "month": 1}


def _dow(value, job):
    """Convert a cron day of week (0-7 or a name) to a systemd day name."""
    if value.isdigit() and int(value) < len(DOW_NAMES):
        return DOW_NAMES[int(value)]
    for name in DOW_NAMES:
        if value.lower() == name.lower():
            return name
    raise AnsibleFilterError(f"pgquartz job {job}: unsupported day of week '{value}', set on_calendar instead")


def _number(value, field, job):
    if not value.isdigit():
        raise AnsibleFilterError(f"pgquartz job {job}: unsupported {field} '{value}', set on_calendar instead")
    return value


def _part(part, field, job):
    """Convert one item of a cron list (e.g. '*', '5', '1-5', '*/15', '5/15')."""
    value, _, step = part.partition("/")
    if step:
        _number(step, field, job)
        if field == "dow":
            raise AnsibleFilterError(f"pgquartz job {job}: steps in day of week are not supported, set on_calendar instead")
        if value == "*":
            return f"{FIELD_START[field]}/{step}"
        start, sep, _ = value.partition("-")
        if sep:
            raise AnsibleFilterError(f"pgquartz job {job}: ranges with steps are not supported, set on_calendar instead")
        return f"{_number(start, field, job)}/{step}"
    if value == "*":
        return "*"
    convert = _dow if field == "dow" else (lambda v, j: _number(v, field, j))
    start, sep, end = value.partition("-")
    if sep:
        return f"{convert(start, job)}..{convert(end, job)}"
    return convert(value, job)


def _field(job, field):
    value = str(job.get(field, "*")).strip() or "*"
    return ",".join(_part(part, field, job.get("name", "")) for part in value.split(","))


def pgquartz_oncalendar(job):
    """Return the systemd OnCalendar expression for a pgquartz job.

    Uses job.on_calendar when set, else converts the cron fields minute, hour, dom, month and dow
    (default '*'). E.g. minute 30, hour 1 -> '*-*-* 1:30:00', dow 1-5 -> 'Mon..Fri *-*-* ...'.
    """
    if not isinstance(job, dict):
        raise AnsibleFilterError("pgquartz_oncalendar expects a job (dict)")
    if job.get("on_calendar"):
        return str(job["on_calendar"])
    dom = _field(job, "dom")
    dow = _field(job, "dow")
    if dom != "*" and dow != "*":
        # cron runs when either matches, systemd only when both match
        raise AnsibleFilterError(
            f"pgquartz job {job.get('name', '')}: both dom and dow are set (cron: either matches), set on_calendar instead"
        )
    calendar = f"*-{_field(job, 'month')}-{dom} {_field(job, 'hour')}:{_field(job, 'minute')}:00"
    if dow != "*":
        calendar = f"{dow} {calendar}"
    return calendar


class FilterModule:
    """pgquartz filters."""

    def filters(self):
        return {"pgquartz_oncalendar": pgquartz_oncalendar}
