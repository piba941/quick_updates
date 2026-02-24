import asyncio
import aiohttp
from datetime import datetime


POLL_URL = "https://status.openai.com/api/v2/incidents.json"
POLL_INTERVAL = 60
seen_incident_ids: set[str] = set()


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
    is_first_poll = True

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

                            # first poll: just collect known IDs
                            if is_first_poll:
                                continue

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

                        if is_first_poll:
                            print(f"[Poller] Seeded {len(seen_incident_ids)} known incidents — watching for new ones")
                            is_first_poll = False

            except Exception as e:
                print(f"[error] {e}")

            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("Tracker is Up")
    asyncio.run(poll_openai())
