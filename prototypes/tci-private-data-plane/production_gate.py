"""Readiness evidence review only. Never deploys or treats local tests as operational consent."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def report():
    gates=json.loads((HERE/"PILOT-GATES.json").read_text())["gates"]
    template=json.loads((HERE/"PRODUCTION-ATTESTATION-TEMPLATE.json").read_text())
    required={g["id"] for g in gates}
    if len(gates)!=13 or required!={f"P{i:02}" for i in range(1,14)} or {g["gateId"] for g in template["attestations"]}!=required:raise ValueError("Required gates incomplete")
    if template["scope"]!="draft_not_approved" or template["productionTarget"]!="not_selected" or any(r["status"]!="not_accepted" for r in template["attestations"]):raise ValueError("Public template may not imply real operational acceptance")
    return {"version":"0.9.5-readiness.1","engineeringEvidenceGates":sum(g["status"]=="local_verified" for g in gates),"requiredOperationalGates":13,"operationalAccepted":0,"productionTarget":"not selected or provisioned","productionReady":False,"releaseLocked":True,"requiresPrivateIndependentEvidence":True,"attestationTemplateSha256":hashlib.sha256((HERE/"PRODUCTION-ATTESTATION-TEMPLATE.json").read_bytes()).hexdigest(),"unacceptedGateIds":sorted(required)}

# A future private review can verify explicit signed readiness records, but never deploy.
def verify_private_attestations(records,trusted_reviewers,evidence_root,target,candidate_commit):
    """Verify evidence bytes and Ed25519 signatures against an independently maintained trust list.
    Cryptographic checks do not establish human independence, legal compliance or factual accuracy.
    """
    import base64,re
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    root=Path(evidence_root).resolve()
    roles={g["id"]:g["owner"] for g in json.loads((HERE/"PILOT-GATES.json").read_text())["gates"]}
    if target not in ("local-operational","private-cloud") or not isinstance(candidate_commit,str) or not re.fullmatch(r"[0-9a-f]{40}",candidate_commit):raise ValueError("Explicit operational target and exact candidate commit required")
    if not isinstance(records,list) or len(records)>13:raise ValueError("Invalid private attestations")
    checked=set()
    for signed in records:
        try:
            r=signed["record"];gid=r["gateId"];reviewer=trusted_reviewers[r["reviewerRef"]]
            if gid not in roles or gid in checked or r["requiredRole"]!=roles[gid] or roles[gid] not in reviewer["roles"]:raise ValueError
            if r["target"]!=target or r["candidateCommit"]!=candidate_commit or r["status"]!="accepted" or not r["reviewDate"] or not r["dispositionRationale"] or not r["approvalReference"]:raise ValueError
            if not isinstance(r["evidence"],list) or not r["evidence"]:raise ValueError
            for item in r["evidence"]:
                p=(root/item["relativePath"]).resolve()
                if not p.is_relative_to(root) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item["sha256"]:raise ValueError
            public=Ed25519PublicKey.from_public_bytes(base64.b64decode(reviewer["publicKey"],validate=True))
            public.verify(base64.b64decode(signed["signature"],validate=True),json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())
        except (InvalidSignature,ValueError,KeyError,TypeError,OSError) as e:raise ValueError("Private attestation or evidence verification failed") from e
        checked.add(gid)
    return {"target":target,"candidateCommit":candidate_commit,"verifiedAttestationCount":len(checked),"unverifiedGateIds":sorted(set(roles)-checked),"allSignedEvidencePresent":len(checked)==13,"releaseLocked":True,"ownerGoNoGoRequired":True,"note":"Review key custody, actual independence and factual evidence; signature verification is not release approval."}

def main():
    import argparse
    p=argparse.ArgumentParser(description="Readiness verification only; never deploy")
    p.add_argument("--private-records");p.add_argument("--trust");p.add_argument("--evidence-root");p.add_argument("--target");p.add_argument("--candidate");a=p.parse_args()
    try:
        fields=[a.private_records,a.trust,a.evidence_root,a.target,a.candidate]
        if not any(fields):result=report()
        elif all(fields):result=verify_private_attestations(json.loads(Path(a.private_records).read_text()),json.loads(Path(a.trust).read_text()),a.evidence_root,a.target,a.candidate)
        else:raise ValueError
        print(json.dumps(result,indent=2))
    except (ValueError,OSError,TypeError,KeyError):raise SystemExit("Readiness review refused; verify explicit private evidence and trusted reviewer records") from None
if __name__=="__main__":main()
