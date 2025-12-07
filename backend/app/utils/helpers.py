from typing import Any, Dict
import json


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """Parse JSON response from Node.js scripts."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from error messages
        lines = response_text.strip().split('\n')
        for line in lines:
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        raise ValueError(f"Could not parse JSON from response: {response_text}")


def validate_solana_address(address: str) -> bool:
    """Basic validation for Solana address format."""
    if not address or len(address) < 32 or len(address) > 44:
        return False
    # Solana addresses are base58 encoded
    # Basic format check (alphanumeric, no confusing characters)
    valid_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
    if not all(c in valid_chars for c in address):
        return False
    return True


def calculate_match_score(skills_match: float, location_match: float, 
                          degree_match: float, experience_match: float, 
                          verified: bool) -> float:
    """Calculate weighted job match score (returns 0-1, not percentage)."""
    score = (
        skills_match * 0.40 +
        location_match * 0.20 +
        degree_match * 0.20 +
        experience_match * 0.10 +
        (1.0 if verified else 0.0) * 0.10
    )
    # Make scores more realistic - cap at 0.95 max, ensure minimum threshold
    score = min(score, 0.95)
    # Only return scores that are meaningful (at least 25% match)
    if score < 0.25:
        return 0.0
    return round(score, 3)  # Return as decimal (0-1)

