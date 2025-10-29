from bento_sts.utility.version_utils import model_version_compare
from bento_sts.pymodels import Model
from functools import cmp_to_key

class MockModel(Model):
    is_latest_version: bool | None = None
    
    
def test_model_version_sorting():
    models = [
        MockModel(name="C3DC", version="10.0.1-9351eb2"),
        MockModel(name="CDS", version="1.6.0-9351eb2"),
        MockModel(name="CDS", version="1.6.0"),
        MockModel(name="CDS", version="1.6.0-04f69bd"),
        MockModel(name="CDS", version="1.5.0"),
        MockModel(name="C3DC", version="10.0.1"),
        MockModel(name="CDS", version="1.9"),
        MockModel(name="CDS", version="1.10.9"),
        MockModel(name="CDS", version="1.10.10"),
        MockModel(name="CDS", version="2.0"),
        MockModel(name="CCDI", version="1.0.0"),
        MockModel(name="CDS", version="1.6.0-0942323"), # this entry checks fallback compare
    ]

    expected = [
        ("C3DC", "10.0.1-9351eb2"),
        ("C3DC", "10.0.1"),
        ("CCDI", "1.0.0"),
        ("CDS", "1.5.0"),
        ("CDS", "1.6.0-04f69bd"),
        ("CDS", "1.6.0-0942323"),
        ("CDS", "1.6.0-9351eb2"),
        ("CDS", "1.6.0"),
        ("CDS", "1.9"),
        ("CDS", "1.10.9"),
        ("CDS", "1.10.10"),
        ("CDS", "2.0")
    ]

    sorted_models = sorted(models, key=cmp_to_key(model_version_compare))
    sorted_names_and_versions = [(m.name, m.version) for m in sorted_models]

    assert sorted_names_and_versions == expected



