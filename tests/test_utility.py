from functools import cmp_to_key
import semver

from src.bento_sts.utility import compare_versions_fallback, extract_semver_base
from src.bento_sts.pymodels import Model


class MockModel:
    def __init__(self, name, version):
        self.name = name
        self.version = version

def test_model_version_sorting():
    models = [
        MockModel("C3DC", "10.0.1-9351eb2"),
        MockModel("CDS", "1.6.0-9351eb2"),
        MockModel("CDS", "1.6.0"),
        MockModel("CDS", "1.6.0-04f69bd"),
        MockModel("CDS", "1.5.0"),
        MockModel("C3DC", "10.0.1"),
        MockModel("CDS", "1.9"),
        MockModel("CDS", "1.10.9"),
        MockModel("CDS", "1.10.10"),
        MockModel("CDS", "2.0"),
        MockModel("CCDI", "1.0.0"),
        MockModel("CDS", "1.6.0-5942323")
    ]

    # Since cmp_to_key can only be used to sort objects, we sort using a custom cmp
    def cmp_model(m: Model, n: Model):
        if m.name == n.name:
            try:
                return semver.compare(m.version, n.version)
            except ValueError:
                m_base = extract_semver_base(m.version)
                n_base = extract_semver_base(n.version)
                res = semver.compare(m_base, n_base)
                if res != 0:
                    return res
                return compare_versions_fallback(m.version, n.version)
        else:
            return -1 if m.name < n.name else 1

    sorted_models = sorted(models, key=cmp_to_key(cmp_model))
    sorted_names_and_versions = [(m.name, m.version) for m in sorted_models]

    expected = [
        ("C3DC", "10.0.1-9351eb2"),
        ("C3DC", "10.0.1"),
        ("CCDI", "1.0.0"),
        ("CDS", "1.5.0"),
        ("CDS", "1.6.0-5942323"),
        ("CDS", "1.6.0-04f69bd"),
        ("CDS", "1.6.0-9351eb2"),
        ("CDS", "1.6.0"),
        ("CDS", "1.9"),
        ("CDS", "1.10.9"),
        ("CDS", "1.10.10"),
        ("CDS", "2.0")
    ]
    assert sorted_names_and_versions == expected


def test_model_versions_sorting():
    """Test version sorting logic from model_model_versions_get with provided data"""
    # Versions as they might come from the database (unsorted)
    ret = ['1.9.1', '2.0.0', '2.1.0', '2.1.0-0338852', '2.1.0-04f69bd', 
           '2.1.0-5942323', '2.1.0-9f42edc', '3.1.0', '3.1.0-03eca65', 
           '3.1.0-bef4a77', '3.1.0-c1af4db', '3.1.0-ce9d6d5']
    
    # Apply the same sorting logic from model_model_versions_get
    def version_compare(v1, v2):
        try:
            return semver.compare(v1, v2)
        except ValueError:
            v1_base = extract_semver_base(v1)
            v2_base = extract_semver_base(v2)
            res = semver.compare(v1_base, v2_base)
            if res != 0:
                return res
            return compare_versions_fallback(v1, v2)
    
    sorted_versions = sorted(ret, key=cmp_to_key(version_compare))
    
    # Expected sorted order - prerelease comes first, then release for same base
    expected = ['1.9.1', '2.0.0', '2.1.0-0338852', '2.1.0-5942323', '2.1.0-04f69bd',
                '2.1.0-9f42edc', '2.1.0', '3.1.0-03eca65', '3.1.0-bef4a77',
                '3.1.0-c1af4db', '3.1.0-ce9d6d5', '3.1.0']
    
    assert sorted_versions == expected


def test_model_versions_correct_sorting():
    """Test that prerelease versions are correctly sorted before release versions"""
    ret = ['1.9.1', '2.0.0', '2.1.0', '2.1.0-0338852', '2.1.0-04f69bd', 
           '2.1.0-5942323', '2.1.0-9f42edc', '3.1.0', '3.1.0-03eca65', 
           '3.1.0-bef4a77', '3.1.0-c1af4db', '3.1.0-ce9d6d5']
    
    def version_compare(v1, v2):
        try:
            return semver.compare(v1, v2)
        except ValueError:
            v1_base = extract_semver_base(v1)
            v2_base = extract_semver_base(v2)
            res = semver.compare(v1_base, v2_base)
            if res != 0:
                return res
            return compare_versions_fallback(v1, v2)
    
    sorted_versions = sorted(ret, key=cmp_to_key(version_compare))
    print(f"\nSorted result with fixed version_utils:")
    print(sorted_versions)
    
    # Expected: prerelease comes first, then release for same base version
    expected = ['1.9.1', '2.0.0', '2.1.0-0338852', '2.1.0-5942323', '2.1.0-04f69bd',
                '2.1.0-9f42edc', '2.1.0', '3.1.0-03eca65', '3.1.0-bef4a77', 
                '3.1.0-c1af4db', '3.1.0-ce9d6d5', '3.1.0']
    
    assert sorted_versions == expected, f"Expected {expected}\nGot {sorted_versions}"