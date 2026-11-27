"""Offline synthetic-only recovery candidate; no network or hosted persistence."""
from datetime import datetime,timezone
import hashlib,hmac,json,secrets,sqlite3,struct
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from data_plane import DataPlane,Invalid

MAGIC=b"TCI-SYNTHETIC-ARCHIVE-1\n"
LIMIT=32*1024*1024
MAX_TEST_RETENTION=30*86400

def _keys(vault,evidence,audit):
    if any(not isinstance(k,bytes) or len(k)!=32 for k in (vault,evidence,audit)) or len({vault,evidence,audit})!=3:raise Invalid("Three independent 32-byte keys required")

def _check(key,archive_id,label):
    return hmac.new(key,(archive_id+":"+label).encode(),hashlib.sha256).hexdigest()

def _verify_db(dp):
    if not dp.verify_audit():raise Invalid("Audit verification failed")
    if dp.db.execute("PRAGMA integrity_check").fetchone()[0]!="ok" or dp.db.execute("PRAGMA foreign_key_check").fetchone():raise Invalid("Database integrity verification failed")
    for r in dp.db.execute("SELECT v.*,a.tenant_id,a.id AS assessment_id FROM versions v JOIN docs d ON v.doc_id=d.id JOIN assessments a ON d.assessment_id=a.id"):
        try:dp._read_bytes({"tenant_id":r["tenant_id"]},r["assessment_id"],r)
        except (InvalidTag,Invalid) as e:raise Invalid("Evidence integrity verification failed") from e

def seal_synthetic(dp,vault_key,retention_seconds,*,confirmed_synthetic=False,clock=None):
    """Seal complete point-in-time database; strip active sessions; never write plaintext backup."""
    if confirmed_synthetic is not True:raise Invalid("Explicit synthetic-only archive confirmation required")
    if type(retention_seconds) is not int or not 1<=retention_seconds<=MAX_TEST_RETENTION:raise Invalid("Synthetic test retention must be 1 second to 30 days")
    _keys(vault_key,dp.key,dp.audit_key);_verify_db(dp)
    now=int(clock() if clock else dp.clock())
    copy=sqlite3.connect(":memory:")
    try:
        dp.db.backup(copy)
        copy.execute("DELETE FROM sessions");copy.commit()
        image=copy.serialize()
    finally:copy.close()
    if len(image)>LIMIT:raise Invalid("Synthetic archive exceeds local test limit")
    id=secrets.token_hex(16)
    header={"format":1,"scope":"synthetic-only","archiveId":id,"createdAt":now,"expiresAt":now+retention_seconds,"registerHash":dp.register_hash,"specHash":dp.spec_hash,"databaseSha256":hashlib.sha256(image).hexdigest(),"evidenceKeyCheck":_check(dp.key,id,"evidence"),"auditKeyCheck":_check(dp.audit_key,id,"audit")}
    meta=json.dumps(header,sort_keys=True,separators=(",",":")).encode();nonce=secrets.token_bytes(12)
    # All metadata and the complete DB image are encrypted and authenticated.
    payload=struct.pack(">I",len(meta))+meta+image
    return MAGIC+nonce+AESGCM(vault_key).encrypt(nonce,payload,MAGIC)

def restore_synthetic(archive,vault_key,evidence_key,audit_key,register,spec,*,confirmed_synthetic=False,clock):
    """Restore exclusively to memory; fail closed before returning an authenticated data plane."""
    if confirmed_synthetic is not True:raise Invalid("Explicit synthetic-only restore confirmation required")
    _keys(vault_key,evidence_key,audit_key)
    if not isinstance(archive,bytes) or not archive.startswith(MAGIC) or len(archive)>LIMIT+65536:raise Invalid("Invalid synthetic archive")
    offset=len(MAGIC)
    try:
        plain=AESGCM(vault_key).decrypt(archive[offset:offset+12],archive[offset+12:],MAGIC)
        size=struct.unpack(">I",plain[:4])[0]
        if not 1<=size<=8192:raise ValueError
        meta=json.loads(plain[4:4+size]);image=plain[4+size:]
        if meta["format"]!=1 or meta["scope"]!="synthetic-only" or not meta["createdAt"]<=int(clock())<meta["expiresAt"] or meta["expiresAt"]-meta["createdAt"]>MAX_TEST_RETENTION:raise ValueError
        if hashlib.sha256(image).hexdigest()!=meta["databaseSha256"]:raise ValueError
        if not hmac.compare_digest(meta["evidenceKeyCheck"],_check(evidence_key,meta["archiveId"],"evidence")) or not hmac.compare_digest(meta["auditKeyCheck"],_check(audit_key,meta["archiveId"],"audit")):raise ValueError
        if hashlib.sha256(Path(register).read_bytes()).hexdigest()!=meta["registerHash"] or hashlib.sha256(Path(spec).read_bytes()).hexdigest()!=meta["specHash"]:raise ValueError
    except (InvalidTag,ValueError,KeyError,TypeError,struct.error) as e:raise Invalid("Archive authentication, key, methodology or retention check failed") from e
    dp=DataPlane(":memory:",evidence_key,audit_key,register,spec,clock=clock)
    try:
        dp.db.deserialize(image)
        dp.db.execute("PRAGMA foreign_keys=ON")
        if dp.db.execute("SELECT count(*) FROM sessions").fetchone()[0]:raise Invalid("Session restoration prohibited")
        _verify_db(dp)
        return dp
    except Exception:
        dp.close();raise

def write_synthetic_archive(path,archive):
    """Create a new owner-only encrypted file; never replace existing data."""
    import os
    if not isinstance(archive,bytes) or not archive.startswith(MAGIC):raise Invalid("Only sealed synthetic archives may be written")
    p=Path(path)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb") as f:f.write(archive);f.flush();os.fsync(f.fileno())
    except Exception:
        # Leave an incomplete encrypted file for explicit operator disposition; no silent deletion.
        raise
    return p
