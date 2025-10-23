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
    Fallback version comparison for non-standard version strings.
    
    Extracts base version (X.Y.Z) and compares using semver.
    Returns -1 if version1 < version2, 0 if equal, 1 if greater.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    m_base = extract_semver_base(version1)
    n_base = extract_semver_base(version2)
    
    # If either base is invalid, compare as strings
    if not m_base or not n_base:
        return -1 if version1 < version2 else (0 if version1 == version2 else 1)
    
    # Compare base versions using semver
    try:
        res = semver.compare(m_base, n_base)
        if res != 0:
            return res
    except (ValueError, TypeError):
        # If semver compare fails, compare as strings
        return -1 if version1 < version2 else (0 if version1 == version2 else 1)
    
    # Base versions are equal, handle prerelease comparison
    if version1 == version2:
        return 0
    
    # Prerelease versions < release versions (semver standard)
    has_pre1 = '-' in version1
    has_pre2 = '-' in version2
    
    if has_pre1 and not has_pre2:
        return -1  # version1 is prerelease, version2 is release
    elif not has_pre1 and has_pre2:
        return 1   # version1 is release, version2 is prerelease
    else:
        # Both are prerelease or both are release, compare full strings
        return -1 if version1 < version2 else (0 if version1 == version2 else 1)