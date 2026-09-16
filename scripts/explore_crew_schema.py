#!/usr/bin/env python3
"""Explore Crew GraphQL schema to find reserve pockets."""
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
    
    print("=== Account with billReserve and balanceLastRefreshed ===")
    result = crew_query(token, """
        query {
            currentUser {
                accounts {
                    id
                    displayName
                    balanceLastRefreshed
                    billReserve {
                        id
                        name
                        balance
                        goal
                        type
                    }
                    balanceOverTime {
                        date
                        balance
                    }
                    subaccounts {
                        id
                        name
                        overallBalance
                        goal
                        isPrimary
                        type
                    }
                }
            }
        }
    """)
    if "errors" in result:
        print(f"Errors: {result['errors']}")
    else:
        accounts = result["data"]["currentUser"]["accounts"]
        for account in accounts:
            print(f"\nAccount: {account['displayName']} ({account['id']})")
            print(f"  balanceLastRefreshed: {account.get('balanceLastRefreshed')}")
            
            bill_reserve = account.get("billReserve")
            if bill_reserve:
                print(f"  billReserve:")
                if isinstance(bill_reserve, list):
                    for r in bill_reserve:
                        print(f"    {r.get('name')}: balance={r.get('balance')} goal={r.get('goal')} type={r.get('type')}")
                elif isinstance(bill_reserve, dict):
                    print(f"    {bill_reserve.get('name')}: balance={bill_reserve.get('balance')}")
            else:
                print(f"  billReserve: {bill_reserve}")
            
            subaccounts = account.get("subaccounts", [])
            print(f"  subaccounts ({len(subaccounts)}):")
            for sub in subaccounts:
                print(f"    {sub['name']:30s} balance={sub.get('overallBalance')} type={sub.get('type')}")
    
    print("\n\n=== Introspection: BillReserve type ===")
    result = crew_query(token, """
        query {
            __type(name: "BillReserve") {
                fields {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
        }
    """)
    if "data" in result and result["data"]:
        fields = result["data"]["__type"]["fields"]
        for f in fields:
            print(f"  {f['name']}: {f['type'].get('name')}")
    else:
        print(result)
    
    print("\n\n=== Introspection: Subaccount type fields ===")
    result = crew_query(token, """
        query {
            __type(name: "Subaccount") {
                fields {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
        }
    """)
    if "data" in result and result["data"]:
        fields = result["data"]["__type"]["fields"]
        for f in fields:
            print(f"  {f['name']}: {f['type'].get('name')}")

if __name__ == "__main__":
    main()
