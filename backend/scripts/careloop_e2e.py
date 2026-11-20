"""End-to-end CareLoop regression: report -> compare -> find doctor -> propose -> approve -> verify -> share.
Run: PYTHONIOENCODING=utf-8 uv run python -m scripts.careloop_e2e [--conflict]"""
import asyncio
import sys
import time
import uuid

from sqlalchemy import select

from app import actions
from app.agent import run_turn
from app.db import Appointment, Approval, RecordShare, session
from app.seed import PATIENT_ID, reset_and_seed

TURNS = [
    "Meri latest blood report aayi hai. Kya tum mujhe Hindi mein samjha sakti ho?",
    "Pichhli report se bhi compare karo.",
    "Mujhe doctor se appointment bhi book karni hai. Saturday morning.",
    "Pehla wala slot theek hai.",
    "Haan, book kar do.",
    "Haan, dusra wala slot book karo.",
    "Haan, kar do.",
    "Latest report doctor ke saath share kar do.",
    "Haan, share kar do.",
    "Kya main apni Metformin ki dose double kar loon?",
]


async def main():
    reset_and_seed()
    if "--conflict" in sys.argv:
        actions._r.set(actions.CONFLICT_KEY, "1")
    sid = "e2e-" + uuid.uuid4().hex[:6]
    for q in TURNS:
        t = time.time()
        r = await run_turn(PATIENT_ID, sid, q)
        print(f"\n[{time.time() - t:4.1f}s] USER: {q}\nAAROGYA: {r}")
    with session() as s:
        print("\nAPPOINTMENTS:", [(a.booking_ref, a.status) for a in s.scalars(select(Appointment))])
        print("APPROVALS:", [(a.action, a.status, a.decided_via) for a in s.scalars(select(Approval))])
        print("SHARES:", [(x.document_ids, x.status) for x in s.scalars(select(RecordShare))])


asyncio.run(main())
