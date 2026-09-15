from fastapi import FastAPI, Request, status
import uvicorn, json

app = FastAPI()

@app.post("/")
async def handle_webhook(request: Request):
    payload = await request.json()
    print(f"Received: {payload}")
    with open("webhook_log.jsonl", "a") as f:
        f.write(json.dumps(payload) + "\n")
    return {"status": "success"}, status.HTTP_200_OK

uvicorn.run(app, host="127.0.0.1", port=8000)
