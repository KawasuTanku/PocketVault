"""Crew GraphQL API client.

Uses the unofficial Crew API (https://api.trycrew.com/willow/graphql)
to fetch pocket data and balances.
"""
import json
import os
import urllib.request
from typing import Optional

CREW_API_URL = "https://api.trycrew.com/willow/graphql"

# GraphQL queries
QUERY_CURRENT_USER = """
query CurrentUser {
    currentUser {
        accounts {
            id
            displayName
            type
            mask
            billReserve {
                nextFundingDate
                totalReservedAmount
                estimatedNextFundingAmount
                settings {
                    funding {
                        subaccount {
                            displayName
                        }
                    }
                }
            }
            subaccounts {
                id
                name
                displayName
                overallBalance
                clearedBalance
                goal
                type
                status
                isPrimary
                piggyBanked
                belongsToCurrentUser
                isExternalAccount
                isChildAccount
                owner {
                    displayName
                }
                account {
                    id
                    displayName
                }
            }
        }
    }
}
"""


def get_bearer_token() -> Optional[str]:
    """Get Crew bearer token from config."""
    token = os.environ.get("CREW_BEARER_TOKEN", "")
    if token:
        return token
    # Try loading from .env
    from pocketvault.database import get_env_path
    env_path = get_env_path()
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("CREW_BEARER_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def crew_query(query: str, variables: Optional[dict] = None, token: Optional[str] = None) -> dict:
    """Send a GraphQL query to Crew API."""
    if token is None:
        token = get_bearer_token()
    if not token:
        raise ValueError("No Crew bearer token available. Set CREW_BEARER_TOKEN env var or add to .env file.")
    
    # Clean token — remove non-ASCII
    token = token.encode('ascii', errors='ignore').decode('ascii')
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    req = urllib.request.Request(
        CREW_API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_accounts(token: Optional[str] = None) -> list[dict]:
    """Fetch all accounts from Crew."""
    result = crew_query(QUERY_CURRENT_USER, token=token)
    if "errors" in result:
        raise RuntimeError(f"Crew API error: {result['errors']}")
    return result.get("data", {}).get("currentUser", {}).get("accounts", [])


def fetch_pockets(token: Optional[str] = None) -> list[dict]:
    """Fetch all pockets (subaccounts) from Crew.
    
    Returns list of pocket dicts with:
    - crew_id: stable subaccount ID
    - name: pocket name
    - display_name: system display name (may differ from name)
    - balance: overall balance in cents
    - goal: goal amount in cents (optional)
    - type: SUBACCOUNT
    - is_primary: whether this is the primary pocket
    - piggy_banked: whether pocket is piggy banked
    - owner: owner display name
    - account_id: parent account ID
    - account_name: parent account display name
    """
    accounts = fetch_accounts(token)
    pockets = []
    for account in accounts:
        for sub in account.get("subaccounts", []):
            pockets.append({
                "crew_id": sub["id"],
                "name": sub.get("name", ""),
                "display_name": sub.get("displayName", sub.get("name", "")),
                "balance": sub.get("overallBalance"),
                "goal": sub.get("goal"),
                "type": sub.get("type"),
                "is_primary": sub.get("isPrimary", False),
                "piggy_banked": sub.get("piggyBanked", False),
                "owner": sub.get("owner", {}).get("displayName", ""),
                "account_id": sub.get("account", {}).get("id", ""),
                "account_name": sub.get("account", {}).get("displayName", ""),
            })
    return pockets


def fetch_autopilot_reserve(token: Optional[str] = None) -> Optional[dict]:
    """Fetch Autopilot Reserve (billReserve) info from Crew."""
    accounts = fetch_accounts(token)
    for account in accounts:
        bill_reserve = account.get("billReserve")
        if bill_reserve:
            settings = bill_reserve.get("settings", {})
            funding = settings.get("funding", {})
            sub = funding.get("subaccount", {})
            return {
                "next_funding_date": bill_reserve.get("nextFundingDate"),
                "total_reserved": bill_reserve.get("totalReservedAmount"),
                "estimated_next_funding": bill_reserve.get("estimatedNextFundingAmount"),
                "funding_subaccount": sub.get("displayName", ""),
            }
    return None
