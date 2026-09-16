"""M2 content-return states, independent of retry path; legacy rules stay versioned."""
try:
    from . import five_band_metrics as previous
except ImportError:
    import five_band_metrics as previous

VERSION = 'v2-body-state-2026-09-14'


def aggregate(items):
    return previous.aggregate(items, body_state=True)


def template(rows):
    value = previous.template(rows)
    value['rubric_version'] = VERSION
    obs = value['metrics'][1]['observation']
    for target in obs['targets']:
        target.update(return_kind='unknown', state_basis='')
    obs['aggregate'] = aggregate(obs['targets'])
    return value


def validate(rows, value, *, coverage=False):
    return previous.validate(rows, value, body_state=True, coverage=coverage)
