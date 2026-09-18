import pytest
from app.locations import code_conflict, site_code
from app.matching import suggest
from tests.test_matching import records, Encoder


@pytest.mark.parametrize('left,right', [
    ('Shelter A', 'Barınak B'), ('Καταφύγιο Α', 'Shelter B'),
    ('School 12', '13 okulu'), ('Σχολείο Β', 'School C'),
    ('Camp 24', 'Kamp 25'), ('A', 'B'),
])
def test_explicit_code_conflicts(left, right):
    assert code_conflict(left, right)
    assert code_conflict(right, left)


@pytest.mark.parametrize('left,right', [
    ('Barınak A', 'Καταφύγιο Α'), ('School B', 'Σχολείο Β'),
    ('  SHELTER  12 ', '12 barınak'), ('İzmir', 'Athens'),
    ('Shelter A near school B', 'Shelter B'), ('North Shelter', 'South Shelter'),
    ('Camp A', 'School B'), ('A-12', 'A-13'), ('', 'A'),
])
def test_unknown_or_compatible_labels_do_not_prove_conflict(left, right):
    assert not code_conflict(left, right)


def test_same_code_is_not_verified_identity():
    r, e, source = records()
    result = suggest(r, [(e, [source])], Encoder([.95]))
    assert 'location_unverified' in result['candidates'][0]['flags']
    assert not suggest(r, [(e, [source])], Encoder([.1]))['candidates']


def test_high_similarity_cannot_override_conflict_and_exclusion_is_visible():
    r, e, source = records()
    e['location'] = source['location'] = 'Shelter B'
    groups = [(e, [source])]
    assert suggest(r, groups, Encoder([.99]), location_guard=False)['candidates']
    result = suggest(r, groups, Encoder([.99]))
    assert not result['candidates']
    assert result['matching']['excluded_locations'] == [
        {'event_id': 'event', 'location': 'Shelter B', 'reason': 'site_code_conflict'}]
    assert not result['automatic_linking']
