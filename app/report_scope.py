"""Reviewer supplied scope. These labels are not model predictions."""
NON_FACTUAL = {'hypothetical', 'general_info'}


def group_key(value):
    return ' '.join((value or '').casefold().split()) or None


def known_group_refs(event, linked=()):
    return sorted({key for r in (event, *linked) if (key := group_key(r.get('group_ref')))})


def group_conflict(report, event, linked=()):
    a = group_key(report.get('group_ref'))
    return bool(a and any(a != b for b in known_group_refs(event, linked)))


def report_warnings(report):
    flags = []
    if report.get('statement_type', 'unknown') == 'unknown':
        flags.append('statement_type_unknown')
    if not group_key(report.get('group_ref')):
        flags.append('group_unknown')
    return flags
