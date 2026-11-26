"""Provider-neutral readiness review. This tool cannot provision, deploy or enable real data."""
from __future__ import annotations
import json,argparse
from pathlib import Path
REQUIRED={
 "hosting":["provider","region","decisionRef"],
 "network":["privateIngress","tls","egressAllowlist"],
 "identity":["provider","mfa","tenantIsolation","immutableHumanIdentity"],
 "storage":["databaseService","privateObjectStore","managedKeyService","metadataEncryption","backupRestorePolicy"],
 "processing":["screeningService","parserIsolation","approvedModelProcessor","modelEgressPolicy"],
 "governance":["retentionPolicy","legalHoldPolicy","deletionVerification","incidentOwner","clientConsentAndContractRef"]
}
TRUE_REQUIRED={("network","privateIngress"),("network","tls"),("identity","mfa"),("identity","tenantIsolation"),("identity","immutableHumanIdentity"),("storage","metadataEncryption"),("processing","parserIsolation")}
def review(config):
    blockers=[]
    if not isinstance(config,dict):config={};blockers.append("Invalid manifest object")
    if config.get("schemaVersion")!="1.0" or config.get("environment")!="private-pilot":blockers.append("Invalid private pilot manifest version or environment")
    if config.get("deploymentAuthorised") is not False or config.get("realClientDataAuthorised") is not False:blockers.append("Preparation manifest must never authorise deployment or real client data")
    for section,keys in REQUIRED.items():
        obj=config.get(section)
        if not isinstance(obj,dict):blockers.append(section+" missing");continue
        for key in keys:
            value=obj.get(key)
            if (section,key) in TRUE_REQUIRED:
                if value is not True:blockers.append(section+"."+key+" not confirmed")
            elif not isinstance(value,str) or not value.strip():blockers.append(section+"."+key+" decision outstanding")
    if not isinstance(config.get("hosting"),dict) or config["hosting"].get("subprocessorsApproved") is not True:blockers.append("Hosting/processor approvals outstanding")
    if not isinstance(config.get("network"),dict) or config["network"].get("publicEvidenceUrls") is not False:blockers.append("Public evidence URLs must be prohibited")
    evidence=config.get("acceptanceEvidence")
    if not isinstance(evidence,dict):evidence={}
    for i in range(1,13):
        key=f"SE-{i:02}"
        row=evidence.get(key)
        if not isinstance(row,dict) or row.get("status")!="reviewed_pass" or not isinstance(row.get("evidenceRef"),str) or not row.get("evidenceRef","").strip() or not isinstance(row.get("reviewer"),str) or not row.get("reviewer","").strip():blockers.append(key+" independently reviewed evidence outstanding")
    if not isinstance(config.get("ownerApproval"),str) or not config["ownerApproval"].strip():blockers.append("Formal owner release decision outstanding")
    return {"status":"blocked" if blockers else "ready_for_formal_review_not_release","blockers":blockers,"deploymentEnabled":False,"realClientDataEnabled":False,"scoringEnabled":False,"note":"Completeness check only; evidence references and approvals must be independently verified."}
def main():
    p=argparse.ArgumentParser();p.add_argument("manifest",nargs="?",default=str(Path(__file__).with_name("pilot-config.example.json")));a=p.parse_args()
    print(json.dumps(review(json.loads(Path(a.manifest).read_text())),indent=2))
if __name__=="__main__":main()
