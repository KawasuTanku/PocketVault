from fastapi import FastAPI, Request, status
import uvicorn, json

app = FastAPI()

@app.post("/")
async def handle_webhook(request: Request):
    payload = await request.json()
    print(f"Received: {payload}")
    with open("/tmp/webhook_log.jsonl", "a") as f:
        f.write(json.dumps(payload) + "\n")
    return {"status": "success"}, status.HTTP_200_OK

uvicorn.run(app, host="74.208.44.202", port=443, ssl_certfile="/tmp/cert.pem", ssl_keyfile="/tmp/key.pem")
