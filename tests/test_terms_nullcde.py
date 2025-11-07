import pytest
from pdb import set_trace

null_pvs = {'Not Assessed', 'Not Asked', 'Temporarily Unavailable', 'Insufficient Quantity', 'Technical Problem', 'Response Declined', 'Not Specified', 'Unknown', 'Not Evaluable', 'Not Reported', 'Not Otherwise Specified', 'Not Applicable', 'Not Allowed To Collect', 'Censored'}

def test_all_pvs_with_nullCDE(test_sts_client):
    response = test_sts_client.get("/v2/terms/all-pvs")
    assert response.status_code == 200
    content = response.json()
    entries_with_null_cde = [x for x in content if [y for y in x[3] if y['useNullCDE']]]
    assert len(entries_with_null_cde) >= 3
    # this picks through the custom json return structure to get the value list:
    pvs_for_gc_library_layout = [pv['value'] for pv in
                                 [x for x in entries_with_null_cde if
                                  [y for y in x[3] if
                                   y['property'] == 'genomic_info.library_layout' and
                                   y['model'] == 'CDS']][0][4]]
    # check if all null_pvs are in the pvs returned for library layout:
    assert null_pvs < set(pvs_for_gc_library_layout)
    # check that the model-specified values are also returned:
    assert set(["Paired-End", "Single-indexed"]) < set(pvs_for_gc_library_layout)
    pass
