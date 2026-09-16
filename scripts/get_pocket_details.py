#!/usr/bin/env python3
"""Get full details on a single Crew pocket (subaccount)."""
import json, sys, urllib.request

URL = "https://api.trycrew.com/willow/graphql"

def crew_query(token, query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    token = sys.argv[1] if len(sys.argv) > 1 else input("Bearer token: ").strip()
    token = token.encode('ascii', errors='ignore').decode('ascii')
    
    pocket_id = sys.argv[2] if len(sys.argv) > 2 else input("Pocket ID: ").strip()
    
    print(f"=== Pocket Details: {pocket_id[:20]}... ===")
    result = crew_query(token, """
        query($id: ID!) {
            node(id: $id) {
                ... on Subaccount {
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
    """, {"id": pocket_id})
    
    if "errors" in result:
        print(f"Errors: {result['errors']}")
        return
    
    node = result.get("data", {}).get("node", {})
    if not node:
        print("Pocket not found")
        return
    
    bal = node.get("overallBalance")
    cleared = node.get("clearedBalance")
    goal = node.get("goal")
    
    print(f"\nName: {node.get('name')}")
    print(f"Display Name: {node.get('displayName')}")
    print(f"Type: {node.get('type')}")
    print(f"Status: {node.get('status')}")
    print(f"Overall Balance: ${bal/100:.2f}" if bal is not None else "Overall Balance: None")
    print(f"Cleared Balance: ${cleared/100:.2f}" if cleared is not None else "Cleared Balance: None")
    print(f"Goal: ${goal/100:.2f}" if goal is not None else "Goal: None")
    print(f"Primary: {node.get('isPrimary')}")
    print(f"Piggy Banked: {node.get('piggyBanked')}")
    print(f"Owner: {node.get('owner', {}).get('displayName', 'N/A')}")
    print(f"Account: {node.get('account', {}).get('displayName', 'N/A')}")

if __name__ == "__main__":
    main()
