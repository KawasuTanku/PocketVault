#!/usr/bin/env python3
"""Get full details on a specific Crew account."""
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
    
    account_id = sys.argv[2] if len(sys.argv) > 2 else "QWNjb3VudDoyZTdkYTRmMC03NmEyLTQ3NTktODQzZi1hMWY2NWJkMzM5ZmM="
    
    print(f"=== Account Details: {account_id[:20]}... ===")
    result = crew_query(token, """
        query($id: ID!) {
            node(id: $id) {
                ... on Account {
                    id
                    displayName
                    type
                    mask
                    balanceLastRefreshed
                    overallBalance
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
                        goal
                        isPrimary
                        type
                        status
                        piggyBanked
                        belongsToCurrentUser
                        isExternalAccount
                        isChildAccount
                        owner {
                            displayName
                        }
                        account {
                            id
                        }
                    }
                }
            }
        }
    """, {"id": account_id})
    
    if "errors" in result:
        print(f"Errors: {result['errors']}")
        return
    
    node = result.get("data", {}).get("node", {})
    if not node:
        print("Account not found")
        return
    
    print(f"\nDisplay Name: {node.get('displayName')}")
    print(f"Type: {node.get('type')}")
    print(f"Mask: {node.get('mask')}")
    print(f"Overall Balance: {node.get('overallBalance')}")
    print(f"Balance Last Refreshed: {node.get('balanceLastRefreshed')}")
    
    bill_reserve = node.get("billReserve")
    if bill_reserve:
        print(f"\nBill Reserve:")
        print(f"  Next Funding Date: {bill_reserve.get('nextFundingDate')}")
        print(f"  Total Reserved: {bill_reserve.get('totalReservedAmount')}")
        print(f"  Estimated Next Funding: {bill_reserve.get('estimatedNextFundingAmount')}")
        settings = bill_reserve.get("settings", {})
        funding = settings.get("funding", {})
        sub = funding.get("subaccount", {})
        if sub:
            print(f"  Funding Subaccount: {sub.get('displayName')}")
    
    subaccounts = node.get("subaccounts", [])
    print(f"\nSubaccounts ({len(subaccounts)}):")
    for sub in subaccounts:
        bal = sub.get("overallBalance")
        goal = sub.get("goal")
        bal_str = f"${bal/100:.2f}" if bal is not None else "None"
        goal_str = f"${goal/100:.2f}" if goal is not None else "None"
        print(f"  {sub.get('name'):30s} balance={bal_str:>12} goal={goal_str:>12} type={sub.get('type')} primary={sub.get('isPrimary')} piggy={sub.get('piggyBanked')} owner={sub.get('owner', {}).get('displayName', 'N/A')}")

if __name__ == "__main__":
    main()
