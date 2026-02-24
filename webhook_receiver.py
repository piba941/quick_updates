from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio
import aiohttp
import uvicorn
import os


seen_incident_ids: set[str] = set()
POLL_URL = "https://status.openai.com/api/v2/incidents.json"
POLL_INTERVAL = 60


def format_status(status: str) -> str:
    return status.replace("_", " ").title()


def log_event(product: str, status: str, message: str = ""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Product: {product}")
    print(f"Status: {status}")
    if message:
        print(f"Message - {message}")
    print("-" * 60)


async def poll_openai():
    etag = None
    last_modified = None

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                headers = {}
                if etag:
                    headers["If-None-Match"] = etag
                if last_modified:
                    headers["If-Modified-Since"] = last_modified

                async with session.get(POLL_URL, headers=headers) as resp:

                    if resp.status == 304:
                        pass  # nothing changed

                    elif resp.status == 200:
                        etag = resp.headers.get("ETag")
                        last_modified = resp.headers.get("Last-Modified")
                        data = await resp.json()

                        for incident in data.get("incidents", []):
                            iid = incident.get("id")
                            if iid in seen_incident_ids:
                                continue
                            seen_incident_ids.add(iid)

                            name = incident.get("name", "Unknown Incident")
                            status = format_status(incident.get("status", "unknown"))
                            impact = incident.get("impact", "unknown").title()
                            affected = [
                                c["name"] for c in incident.get("components", [])
                                if "name" in c
                            ]
                            affected_str = ", ".join(affected) if affected else "OpenAI API"
                            updates = incident.get("incident_updates", [])
                            message = updates[0].get("body", "") if updates else ""

                            log_event(
                                product=f"OpenAI API - {affected_str}",
                                status=f"{name} — {status} ({impact} impact)",
                                message=message,
                            )

            except Exception as e:
                print(f"[error] {e}")

            await asyncio.sleep(POLL_INTERVAL)



@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_openai())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    if "component_update" in payload:
        update = payload["component_update"]
        component = payload.get("component", {})
        name = component.get("name") or update.get("name", "Unknown Service")
        new_status = format_status(update.get("new_status", "unknown"))
        log_event(product=f"OpenAI API - {name}", status=new_status)

    elif "incident" in payload:
        incident = payload["incident"]
        name = incident.get("name", "Unnamed Incident")
        status = format_status(incident.get("status", "unknown"))
        impact = incident.get("impact", "unknown").title()
        affected = [c["name"] for c in incident.get("components", []) if "name" in c]
        affected_str = ", ".join(affected) if affected else "Unknown"
        updates = incident.get("incident_updates", [])
        message = updates[0].get("body", "") if updates else ""
        log_event(
            product=f"OpenAI API - {affected_str}",
            status=f"{name} — {status} ({impact} impact)",
            message=message,
        )

    else:
        print(f"Unknown payload received")

    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("webhook_receiver:app", host="0.0.0.0", port=port)
