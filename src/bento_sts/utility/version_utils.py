import re
import semver

def extract_semver_base(version_str):
    """Extract X.Y.Z from version string: "1.6.0-9351eb2" → "1.6.0", "1.9" → "1.9.0" """
    if not version_str:
        return None
    match = re.match(r'(\d+\.\d+(?:\.\d+)?)(?:-(.+))?', version_str)
    if match:
        base = match.group(1)
        # Pad to X.Y.Z format
        parts = base.split('.')
        while len(parts) < 3:
            parts.append('0')
        return '.'.join(parts)
    return None


def compare_versions_fallback(version1: str, version2: str) -> int:
    """
    Prerelease version comparison when base versions are equal.
    Assumes base versions (X.Y.Z) have already been compared and are equal.
    
    Returns -1 if version1 < version2, 0 if equal, 1 if greater.
    Prerelease versions < release versions (semver standard).
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    # If versions are identical
    if version1 == version2:
        return 0
    
    # Prerelease versions < release versions (prerelease comes first)
    has_pre1 = '-' in version1
    has_pre2 = '-' in version2
    
    if has_pre1 and not has_pre2:
        return -1  # version1 is prerelease, version2 is release (prerelease comes first)
    elif not has_pre1 and has_pre2:
        return 1   # version1 is release, version2 is prerelease (release comes after)
    else:
        # Both are prerelease or both are release
        if not has_pre1 and not has_pre2:
            # Both are release versions, compare as strings
            return -1 if version1 < version2 else (0 if version1 == version2 else 1)
        
        # Both are prerelease - extract and compare suffixes
        pre1 = version1.split('-')[1] if '-' in version1 else ''
        pre2 = version2.split('-')[1] if '-' in version2 else ''
        
        # Compare suffixes as strings
        return -1 if pre1 < pre2 else (0 if pre1 == pre2 else 1)

def model_version_compare(m1, m2):
    if (m1.name == m2.name):
        v1 = m1.version
        v2 = m2.version
        try:
            return semver.compare(v1, v2)
        except ValueError:
            v1_base = extract_semver_base(v1)
            v2_base = extract_semver_base(v2)
            res = semver.compare(v1_base, v2_base)
            if res != 0:
                return res
            return compare_versions_fallback(v1, v2)
    else:
        return -1 if m1.name < m2.name else 1

def version_string_compare(v1, v2):
    try:
        return semver.compare(v1, v2)
    except ValueError:
        v1_base = extract_semver_base(v1)
        v2_base = extract_semver_base(v2)
        res = semver.compare(v1_base, v2_base)
        if res != 0:
            return res
        return compare_versions_fallback(v1, v2)
