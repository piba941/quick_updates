from fastapi import FastAPI, Request
from datetime import datetime
import uvicorn
import os

app = FastAPI()


def format_status(status: str) -> str:
    return status.replace("_", " ").title()


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if "component_update" in payload:
        update = payload["component_update"]
        component = payload.get("component", {})

        name = component.get("name") or update.get("name", "Unknown Service")
        old_status = format_status(update.get("old_status", "unknown"))
        new_status = format_status(update.get("new_status", "unknown"))

        print(f"[{ts}] Product: OpenAI API - {name}")
        print(f"Status: {new_status}")

    elif "incident" in payload:
        incident = payload["incident"]

        name = incident.get("name", "Unnamed Incident")
        status = format_status(incident.get("status", "unknown"))
        impact = incident.get("impact", "unknown").title()

        affected = [c["name"] for c in incident.get("components", []) if "name" in c]
        affected_str = ", ".join(affected) if affected else "Unknown"

        latest_update = ""
        updates = incident.get("incident_updates", [])
        if updates:
            latest_update = updates[0].get("body", "")

        print(f"[{ts}] Product: OpenAI API - {affected_str}")
        print(f"Status: {name} — {status} ({impact} impact)")
        if latest_update:
            print(f"{latest_update}")

    else:
        print(f"[{ts}] Unknown event received")

    print("-" * 60)
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("webhook_receiver:app", host="0.0.0.0", port=port)
