#!/usr/bin/env python3
"""Test Crew GraphQL API — get pocket list and balances."""
import json, sys
import urllib.request

URL = "https://api.trycrew.com/willow/graphql"

def crew_query(token, query, variables=None):
    """Send a GraphQL query to Crew API."""
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
    
    # Clean token — remove non-ASCII characters
    token = token.encode('ascii', errors='ignore').decode('ascii')
    
    if not token:
        print("Error: No token provided")
        return
    
    print(f"\nToken (first 20 chars): {token[:20]}...")
    print("\n=== CurrentUser: Pockets ===")
    result = crew_query(token, """
        query CurrentUser {
            currentUser {
                accounts {
                    id
                    subaccounts {
                        id
                        name
                        overallBalance
                        goal
                        isPrimary
                    }
                }
            }
        }
    """)
    
    if "errors" in result:
        print(f"ERROR: {result['errors']}")
        return
    
    accounts = result.get("data", {}).get("currentUser", {}).get("accounts", [])
    
    all_pockets = []
    for account in accounts:
        for sub in account.get("subaccounts", []):
            all_pockets.append(sub)
    
    # Group by name to show duplicates
    from collections import defaultdict
    by_name = defaultdict(list)
    for p in all_pockets:
        by_name[p["name"]].append(p)
    
    print(f"\nTotal subaccounts: {len(all_pockets)}")
    print(f"Unique names: {len(by_name)}")
    print()
    
    # Show all pockets
    for name, pockets in sorted(by_name.items()):
        if len(pockets) > 1:
            total = sum(p.get("overallBalance") or 0 for p in pockets)
            print(f"  {name} ({len(pockets)} duplicates, combined: ${total/100:.2f})")
            for p in pockets:
                bal = p.get("overallBalance") or 0
                goal = p.get("goal") or 0
                print(f"      ID: {p['id'][:20]}...  Balance: ${bal/100:.2f}  Goal: ${goal/100:.2f}")
        else:
            p = pockets[0]
            bal = p.get("overallBalance") or 0
            goal = p.get("goal") or 0
            print(f"   {name:30s} ${bal/100:>10.2f}  (goal: ${goal/100:.2f})")

if __name__ == "__main__":
    main()
