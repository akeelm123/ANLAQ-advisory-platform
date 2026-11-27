"""Offline design contract check. No cloud API or deployment path."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def require(condition,message):
    if not condition:raise ValueError(message)

def verify_design(d):
    require(d["status"]=="proposed_not_provisioned","Only unprovisioned design permitted")
    require(set(d["authority"])=={"deploymentAuthorised","realClientAuthorised","productionAuthorised","budgetApproved","participantsApproved","identityTenantConfirmed"} and all(v is False for v in d["authority"].values()),"No inferred operational or budget authority")
    s=d["scope"];n=d["network"];i=d["identity"];c=d["compute"];a=d["data"];g=d["acceptance"]
    require(s["provider"]=="AWS" and s["region"]==s["dataRegion"]=="ap-southeast-1" and s["inputClass"]=="fictional-only" and s["environment"]=="isolated-synthetic-pilot" and s["independentReview"] is True,"Proposed synthetic regional scope required")
    require(type(s["cohortLimit"]) is int and 1<=s["cohortLimit"]<=10,"Proposed bounded synthetic cohort")
    for k in ("applicationPublicIngress","applicationPublicIp","databasePublicAccess","externalModelEgress"):require(n[k] is False,"Disallowed network setting: "+k)
    for k in ("internalLoadBalancer","clientVPN","vpnFederatedMfa","privateStorageConnectivity","controlledIdentityEgress","denyPublicObjectAccess"):require(n[k] is True,"Missing network control: "+k)
    require(n["availabilityZones"]==2,"Two-AZ network design required")
    for k in ("mfaRequired","serverSideMembership","distinctReviewer","sessionRevocation"):require(i[k] is True,"Missing identity control: "+k)
    for k in ("selfRegistration","browserTokenPersistence","localPasswordFallback"):require(i[k] is False,"Disallowed identity setting: "+k)
    require(c["syntheticOnly"] is True and c["privateTasks"] is True and c["externalModelsEnabled"] is False and c["pilotScoringEnabled"] is False,"Synthetic private compute only")
    for k in ("customerManagedKeys","separateKeyPurposes","managedSecretStore","scannerIsolation","failClosedIntake","externalAudit","exportDisabled","backupRestoreDrillRequired"):require(a[k] is True,"Missing data control: "+k)
    for k in ("plaintextPersistentEvidence","retentionPolicyApproved"):require(a[k] is False,"Disallowed data setting: "+k)
    require(all(g[k] is False for k in ("designOwnerApproved","independentDesignReviewComplete","providerAccountConfirmed")) and g["operationalGatesAccepted"]==0,"No operational acceptance may be inferred")
    p=d["costPlanning"];require(p["currency"]=="USD" and p["providerQuoteVerified"] is False,"Planning allocations, not provider quote")
    require(len(p["items"])==7 and all(type(x["low"]) is int and type(x["high"]) is int and 0<=x["low"]<=x["high"] for x in p["items"]),"Invalid planning range")
    l=d["localOption"];ln=l["network"];li=l["identity"];lc=l["compute"];ld=l["data"];la=l["acceptance"];lp=l["costPlanning"]
    require(l["status"]=="proposed_not_provisioned" and l["environment"]=="local-machine-synthetic-pilot" and l["inputClass"]=="fictional-only" and type(l["cohortLimit"]) is int and 1<=l["cohortLimit"]<=4,"Local option synthetic scope")
    require(ln["bindAddress"]=="127.0.0.1" and all(ln[k] is False for k in ("lanAccess","publicIngress","remoteAccess","externalModelEgress","cloudSync")),"Local option loopback only; no remote access")
    for k in ("osScreenLock","fileVaultRequired","separateNamedOsAccounts","separateNamedAppAccounts","independentReviewer","sessionRevocation"):require(li[k] is True,"Missing local identity requirement: "+k)
    for k in ("sharedCredentials","browserTokenPersistence","productionIdentityImplemented"):require(li[k] is False,"Disallowed local identity assertion: "+k)
    require(lc["syntheticOnly"] is True and lc["pilotScoringEnabled"] is False and lc["externalModelsEnabled"] is False,"Local synthetic-only runtime")
    for k in ("encryptedVolumeRequired","separateArchiveKeysRequired","encryptedOfflineBackup","scannerIsolationRequired","auditExportRequired","backupRestoreDrillRequired"):require(ld[k] is True,"Missing local data requirement: "+k)
    for k in ("plaintextPersistentEvidence","backupDestinationCloudSync","retentionPolicyApproved"):require(ld[k] is False,"Disallowed local data setting: "+k)
    require(all(la[k] is False for k in ("designOwnerApproved","independentDesignReviewComplete","machineSecurityConfirmed")) and la["operationalGatesAccepted"]==0,"No local operational approval inferred")
    require(lp["currency"]=="USD" and lp["providerQuoteVerified"] is False and 0<=lp["monthlyIncrementalLow"]<=lp["monthlyIncrementalHigh"],"Local planning range required")
    return {"localOption":{"designContract":"local checks pass","deployment":"blocked","monthlyIncrementalPlanningUsd":{"low":lp["monthlyIncrementalLow"],"high":lp["monthlyIncrementalHigh"]}},"version":d["version"],"designContract":"local checks pass","deployment":"blocked","operationalGatesAccepted":0,"monthlyPlanningUsd":{"low":sum(x["low"] for x in p["items"]),"high":sum(x["high"] for x in p["items"])},"providerQuoteVerified":False}

if __name__=="__main__":print(json.dumps(verify_design(json.loads((HERE/"PRIVATE-PILOT-ARCHITECTURE.json").read_text())),indent=2))
