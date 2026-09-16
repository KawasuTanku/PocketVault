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
    
    print("=== Introspection: Account type fields ===")
    result = crew_query(token, """
        query {
            __type(name: "Account") {
                fields {
                    name
                    type {
                        name
                        kind
                        ofType {
                            name
                            kind
                        }
                    }
                }
            }
        }
    """)
    if "data" in result:
        fields = result["data"]["__type"]["fields"]
        for f in fields:
            print(f"  {f['name']}: {f['type'].get('name') or f['type'].get('ofType',{}).get('name')}")
    
    print("\n=== Introspection: Subaccount type fields ===")
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
    if "data" in result:
        fields = result["data"]["__type"]["fields"]
        for f in fields:
            print(f"  {f['name']}: {f['type'].get('name')}")
    
    print("\n=== Try querying accounts with different fields ===")
    result = crew_query(token, """
        query {
            currentUser {
                accounts {
                    id
                    type
                    balance
                    pockets {
                        id
                        name
                        balance
                        type
                    }
                    reserves {
                        id
                        name
                        balance
                    }
                }
            }
        }
    """)
    print(json.dumps(result, indent=2)[:3000])
    
    print("\n=== Try node query for account ===")
    result = crew_query(token, """
        query {
            currentUser {
                accounts {
                    id
                }
            }
        }
    """)
    if "data" in result:
        accounts = result["data"]["currentUser"]["accounts"]
        if accounts:
            account_id = accounts[0]["id"]
            print(f"First account ID: {account_id}")
            
            # Try to get account details with different fields
            result2 = crew_query(token, """
                query($id: ID!) {
                    node(id: $id) {
                        ... on Account {
                            id
                            pockets {
                                id
                                name
                                balance
                                type
                            }
                            subaccounts {
                                id
                                name
                                type
                            }
                        }
                    }
                }
            """, {"id": account_id})
            print(json.dumps(result2, indent=2)[:3000])

if __name__ == "__main__":
    main()
