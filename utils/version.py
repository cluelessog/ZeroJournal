"""
Version and deployment information utility
"""

import os
from datetime import datetime
from pathlib import Path

# Application version
APP_VERSION = "1.5.0"
APP_NAME = "ZeroJournal"

# Cache for deployment info to avoid repeated calls
_deployment_info_cache = None

def get_git_commit_hash() -> str:
    """
    Get the current git commit hash.
    Returns short hash or 'unknown' if git is not available.
    """
    # Try to read from environment variable first (common in deployment platforms)
    git_commit = os.environ.get('GIT_COMMIT') or os.environ.get('COMMIT_SHA') or os.environ.get('HEROKU_SLUG_COMMIT')
    if git_commit:
        return str(git_commit)[:7]
    
    # Try git command as fallback (may not work in all deployment environments)
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=2,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (Exception, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return 'unknown'

def get_deployment_info() -> dict:
    """
    Get deployment information including version, commit hash, and deployment date.
    
    Returns:
        dict with keys: version, commit_hash, deployment_date, environment
    """
    global _deployment_info_cache
    if _deployment_info_cache is not None:
        return _deployment_info_cache
    
    try:
        commit_hash = get_git_commit_hash()
    except Exception:
        commit_hash = 'unknown'
    
    try:
        # Try to get deployment date from environment or use current time
        deployment_date = os.environ.get('DEPLOYMENT_DATE', datetime.now().strftime('%Y-%m-%d'))
    except Exception:
        deployment_date = datetime.now().strftime('%Y-%m-%d')
    
    # Detect environment
    environment = 'production'
    try:
        if os.environ.get('STREAMLIT_SERVER_ENVIRONMENT'):
            environment = os.environ.get('STREAMLIT_SERVER_ENVIRONMENT', 'production')
        elif os.environ.get('STREAMLIT_CLOUD'):
            environment = 'streamlit-cloud'
    except Exception:
        pass
    
    _deployment_info_cache = {
        'version': APP_VERSION,
        'commit_hash': commit_hash,
        'deployment_date': deployment_date,
        'environment': environment,
        'app_name': APP_NAME
    }
    
    return _deployment_info_cache

def get_version_string() -> str:
    """
    Get a formatted version string for display.
    
    Returns:
        Formatted string like "v1.5.0 (abc1234)"
    """
    try:
        info = get_deployment_info()
        return f"v{info.get('version', APP_VERSION)} ({info.get('commit_hash', 'unknown')})"
    except Exception:
        return f"v{APP_VERSION} (unknown)"

def get_full_version_info() -> str:
    """
    Get full version information as a formatted string.
    
    Returns:
        Multi-line string with all version details
    """
    info = get_deployment_info()
    return f"""
**Version:** {info['version']}  
**Commit:** {info['commit_hash']}  
**Deployed:** {info['deployment_date']}  
**Environment:** {info['environment']}
"""
