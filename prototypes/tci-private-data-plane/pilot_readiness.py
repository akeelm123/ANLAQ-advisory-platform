"""Local readiness reporting; cannot provision infrastructure or approve release."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def report():
    data=json.loads((HERE/"PILOT-GATES.json").read_text())
    gates=data["gates"]
    if {g["id"] for g in gates}!={f"P{i:02}" for i in range(1,14)} or len(gates)!=13:raise ValueError("Required readiness gates missing")
    if data["mode"]!="synthetic-local-only" or data["deploymentAuthorised"] is not False or data["realClientAuthorised"] is not False:raise ValueError("Readiness package is synthetic only")
    if any(g["status"] not in {"open","local_verified"} for g in gates):raise ValueError("Local report cannot authorise operational approval")
    return {"version":data["version"],"requiredGates":len(gates),"localVerified":sum(g["status"]=="local_verified" for g in gates),"operationalAccepted":0,"pilotDeployment":"blocked","production":"locked","gates":gates}

if __name__=="__main__":print(json.dumps(report(),indent=2))
