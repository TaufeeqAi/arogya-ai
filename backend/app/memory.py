"""Personal Health Memory Engine: structured (Postgres) + semantic (Qdrant) memory, deterministic comparison."""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import select

from .config import get_settings
from .db import Document, Observation, session

COLLECTION = "aarogya_record_chunks"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


# ---------------------------------------------------------------- structured memory
def obs_dict(o: Observation, doc: Document | None = None) -> dict:
    return {
        "observation_id": o.id,
        "test_code": o.test_code,
        "test_name": o.test_name,
        "value": o.value,
        "unit": o.unit,
        "reference_range": o.ref_text,
        "ref_low": o.ref_low,
        "ref_high": o.ref_high,
        "lab_flag": {"H": "above lab range", "L": "below lab range"}.get(o.lab_flag, "within lab range"),
        "observed_on": o.observed_on.isoformat(),
        "source": {"document_id": o.document_id, "title": doc.title if doc else "", "page": o.page,
                   "source_name": doc.source_name if doc else "", "trust_label": doc.trust_label if doc else ""},
    }


def lab_documents(patient_id: str) -> list[Document]:
    with session() as s:
        return list(s.scalars(select(Document).where(Document.patient_id == patient_id,
                                                     Document.doc_type == "lab_report")
                              .order_by(Document.issued_on.desc())))


def report_observations(patient_id: str, document_id: str) -> tuple[Document | None, list[dict]]:
    with session() as s:
        doc = s.get(Document, document_id)
        if not doc or doc.patient_id != patient_id:
            return None, []
        rows = s.scalars(select(Observation).where(Observation.patient_id == patient_id,
                                                   Observation.document_id == document_id))
        return doc, [obs_dict(o, doc) for o in rows]


def compare(patient_id: str, test_codes: list[str] | None = None) -> dict:
    """Deterministic latest-vs-previous comparison. Only identical test code + unit are compared."""
    with session() as s:
        q = select(Observation, Document).join(Document, Document.id == Observation.document_id).where(
            Observation.patient_id == patient_id).order_by(Observation.observed_on)
        rows = s.execute(q).all()
    series: dict[str, list] = {}
    for o, d in rows:
        if test_codes and o.test_code not in test_codes:
            continue
        series.setdefault(o.test_code, []).append((o, d))
    comparisons, not_comparable = [], []
    for code, pts in series.items():
        if len(pts) < 2:
            not_comparable.append({"test_code": code, "test_name": pts[0][0].test_name,
                                   "reason": "only one measurement on record",
                                   "observed_on": pts[0][0].observed_on.isoformat()})
            continue
        (prev, pd), (latest, ld) = pts[-2], pts[-1]
        if prev.unit != latest.unit:
            not_comparable.append({"test_code": code, "test_name": latest.test_name,
                                   "reason": f"units differ ({prev.unit} vs {latest.unit}); no validated conversion"})
            continue
        diff = round(latest.value - prev.value, 2)
        pct = round(diff / prev.value * 100, 1) if prev.value else None
        comparisons.append({
            "test_code": code, "test_name": latest.test_name, "unit": latest.unit,
            "reference_range": latest.ref_text, "ref_low": latest.ref_low, "ref_high": latest.ref_high,
            "points": [obs_dict(o, d) for o, d in pts],
            "previous": prev.value, "latest": latest.value, "change": diff, "change_pct": pct,
            "direction": "up" if diff > 0 else "down" if diff < 0 else "same",
            "latest_lab_flag": obs_dict(latest)["lab_flag"],
            "reference_range_changed": prev.ref_text != latest.ref_text,
        })
    return {"method": "deterministic-diff v1 (same test code + same unit only; no clinical interpretation)",
            "comparisons": comparisons, "not_comparable": not_comparable}


# ---------------------------------------------------------------- semantic memory (Qdrant)
@lru_cache
def _embedder():
    from fastembed import TextEmbedding
    return TextEmbedding(EMBED_MODEL)


@lru_cache
def _qdrant():
    from qdrant_client import QdrantClient
    return QdrantClient(url=get_settings().qdrant_url, timeout=30, check_compatibility=False)


def _chunks(doc: Document) -> list[str]:
    lines = [l.strip() for l in doc.text.splitlines() if l.strip()]
    out, buf = [], []
    for l in lines:
        buf.append(l)
        if sum(len(x) for x in buf) > 300:
            out.append(" ".join(buf)); buf = []
    if buf:
        out.append(" ".join(buf))
    return out


def index_all_documents(patient_id: str) -> int:
    from qdrant_client.models import Distance, PointStruct, VectorParams
    qc = _qdrant()
    if qc.collection_exists(COLLECTION):
        qc.delete_collection(COLLECTION)
    qc.create_collection(COLLECTION, vectors_config=VectorParams(size=384, distance=Distance.COSINE))
    with session() as s:
        docs = list(s.scalars(select(Document).where(Document.patient_id == patient_id)))
    points, i = [], 0
    for d in docs:
        for c in _chunks(d):
            points.append((c, {"patient_id": patient_id, "document_id": d.id, "title": d.title,
                               "doc_type": d.doc_type, "issued_on": d.issued_on.isoformat(), "text": c}))
    vecs = list(_embedder().embed([p[0] for p in points]))
    qc.upsert(COLLECTION, [PointStruct(id=i, vector=list(v), payload=p[1]) for i, (v, p) in enumerate(zip(vecs, points))])
    return len(points)


def index_document(doc: Document) -> None:
    import uuid
    from qdrant_client.models import PointStruct
    chunks = _chunks(doc)
    vecs = list(_embedder().embed(chunks))
    _qdrant().upsert(COLLECTION, [PointStruct(id=str(uuid.uuid4()), vector=list(v), payload={
        "patient_id": doc.patient_id, "document_id": doc.id, "title": doc.title, "doc_type": doc.doc_type,
        "issued_on": doc.issued_on.isoformat(), "text": c}) for c, v in zip(chunks, vecs)])


def semantic_search(patient_id: str, query: str, k: int = 4) -> list[dict]:
    from qdrant_client.models import FieldCondition, Filter, MatchValue
    try:
        vec = list(next(iter(_embedder().embed([query]))))
        res = _qdrant().query_points(COLLECTION, query=vec, limit=k, query_filter=Filter(
            must=[FieldCondition(key="patient_id", match=MatchValue(value=patient_id))])).points
        return [{"score": round(p.score, 3), **p.payload} for p in res]
    except Exception:
        # Fallback: keyword search over patient-scoped documents
        words = [w.lower() for w in query.split() if len(w) > 3]
        with session() as s:
            docs = list(s.scalars(select(Document).where(Document.patient_id == patient_id)))
        hits = []
        for d in docs:
            for c in _chunks(d):
                score = sum(w in c.lower() for w in words)
                if score:
                    hits.append({"score": score, "document_id": d.id, "title": d.title,
                                 "issued_on": d.issued_on.isoformat(), "text": c})
        return sorted(hits, key=lambda h: -h["score"])[:k]
