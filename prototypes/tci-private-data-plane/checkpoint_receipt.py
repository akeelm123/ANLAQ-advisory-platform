"""Read-only independently signed synthetic checkpoint receipt; no automatic external witness."""
import argparse,base64,getpass,hashlib,json,time
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from local_store import _derive,_private_file
from pilot_storage import restore_synthetic,LIMIT
from serve import REGISTER,SPEC
from data_plane import Invalid

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def make_receipt(archive,keys,register,spec,clock=time.time):
    dp=restore_synthetic(archive,*keys,register,spec,confirmed_synthetic=True,clock=clock)
    try:
        row=dp.db.execute("SELECT seq,mac FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        return {"format":"TCI-synthetic-checkpoint-receipt-v1","archiveSha256":hashlib.sha256(archive).hexdigest(),"auditSeq":row["seq"] if row else 0,"auditHead":row["mac"] if row else "GENESIS","registerHash":dp.register_hash,"specHash":dp.spec_hash,"createdAt":int(clock()),"scope":"synthetic-only"}
    finally:dp.close()
def sign_receipt(receipt,key):
    if not isinstance(key,Ed25519PrivateKey) or receipt.get("format")!="TCI-synthetic-checkpoint-receipt-v1" or receipt.get("scope")!="synthetic-only":raise Invalid("Independent Ed25519 witness key and synthetic receipt required")
    return {"receipt":receipt,"signature":base64.b64encode(key.sign(canonical(receipt))).decode()}
def verify_receipt(signed,archive,public):
    if not isinstance(public,Ed25519PublicKey):raise Invalid("Trusted independent witness public key required")
    try:
        r=signed["receipt"];public.verify(base64.b64decode(signed["signature"],validate=True),canonical(r))
        if r["format"]!="TCI-synthetic-checkpoint-receipt-v1" or r["scope"]!="synthetic-only" or r["archiveSha256"]!=hashlib.sha256(archive).hexdigest():raise ValueError
    except (InvalidSignature,KeyError,ValueError,TypeError) as e:raise Invalid("Receipt does not authenticate this exact archive") from e
    return {"status":"exact_signed_checkpoint_match","auditSeq":r["auditSeq"],"productionAuthorised":False,"note":"Only proves match to supplied trusted receipt; independent latest-receipt custody is required"}
def write_new(path,obj):
    import os
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"wb") as f:f.write(canonical(obj)+b"\n");f.flush();os.fsync(f.fileno())
def main():
    p=argparse.ArgumentParser(description="Read-only synthetic checkpoint witness receipt")
    sub=p.add_subparsers(dest="action",required=True)
    c=sub.add_parser("create");c.add_argument("--archive",required=True);c.add_argument("--salt",required=True);c.add_argument("--out",required=True)
    s=sub.add_parser("sign");s.add_argument("--receipt",required=True);s.add_argument("--witness-key",required=True);s.add_argument("--out",required=True)
    v=sub.add_parser("verify");v.add_argument("--signed",required=True);v.add_argument("--archive",required=True);v.add_argument("--trusted-public-key",required=True)
    a=p.parse_args()
    try:
        if a.action=="create":
            keys=_derive(getpass.getpass("Original vault passphrase: "),_private_file(Path(a.salt),32))
            r=make_receipt(_private_file(Path(a.archive),LIMIT+65536),keys,REGISTER,SPEC);write_new(a.out,r);print("Unsigned authenticated synthetic receipt created; independent witness review required.")
        elif a.action=="sign":
            password=getpass.getpass("Independent witness PEM key password (blank if unencrypted): ").encode() or None
            key=serialization.load_pem_private_key(_private_file(Path(a.witness_key),16384),password=password)
            r=json.loads(_private_file(Path(a.receipt),16384));write_new(a.out,sign_receipt(r,key));print("Witness receipt signed; retain independently outside vault.")
        else:
            public=serialization.load_pem_public_key(Path(a.trusted_public_key).read_bytes())
            result=verify_receipt(json.loads(_private_file(Path(a.signed),16384)),_private_file(Path(a.archive),LIMIT+65536),public);print(json.dumps(result,indent=2))
    except (OSError,ValueError,TypeError,Invalid):raise SystemExit("Receipt operation refused; inspect selected files and trusted witness custody") from None
if __name__=="__main__":main()
