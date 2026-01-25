"""
Version and deployment information utility
"""

import os
from datetime import datetime
from pathlib import Path

# Application version
APP_VERSION = "1.5.0"
APP_NAME = "ZeroJournal"

def get_git_commit_hash() -> str:
    """
    Get the current git commit hash.
    Returns short hash or 'unknown' if git is not available.
    """
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    # Try to read from environment variable (common in deployment platforms)
    return os.environ.get('GIT_COMMIT', 'unknown')[:7] if os.environ.get('GIT_COMMIT') else 'unknown'

def get_deployment_info() -> dict:
    """
    Get deployment information including version, commit hash, and deployment date.
    
    Returns:
        dict with keys: version, commit_hash, deployment_date, environment
    """
    commit_hash = get_git_commit_hash()
    
    # Try to get deployment date from environment or use current time
    deployment_date = os.environ.get('DEPLOYMENT_DATE', datetime.now().strftime('%Y-%m-%d'))
    
    # Detect environment
    environment = 'production'
    if os.environ.get('STREAMLIT_SERVER_ENVIRONMENT'):
        environment = os.environ.get('STREAMLIT_SERVER_ENVIRONMENT', 'production')
    elif os.environ.get('STREAMLIT_CLOUD'):
        environment = 'streamlit-cloud'
    
    return {
        'version': APP_VERSION,
        'commit_hash': commit_hash,
        'deployment_date': deployment_date,
        'environment': environment,
        'app_name': APP_NAME
    }

def get_version_string() -> str:
    """
    Get a formatted version string for display.
    
    Returns:
        Formatted string like "v1.5.0 (abc1234)"
    """
    info = get_deployment_info()
    return f"v{info['version']} ({info['commit_hash']})"

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
