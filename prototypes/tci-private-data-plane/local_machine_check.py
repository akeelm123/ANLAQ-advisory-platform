"""Read-only local machine readiness check; output is private operational evidence."""
import json,platform,shutil,subprocess
from pathlib import Path

def command(args):
    try:
        r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=10,check=False)
        return r.stdout.strip() if r.returncode==0 else None
    except (OSError,subprocess.SubprocessError):return None

def filevault_status(text):
    if not isinstance(text,str):return "unverified"
    if "FileVault is On." in text:return "on"
    if "FileVault is Off." in text:return "off"
    return "unverified"

def check():
    memory=command(["sysctl","-n","hw.memsize"])
    try:gib=round(int(memory)/1024**3,2)
    except (ValueError,TypeError):gib=None
    fv=filevault_status(command(["fdesetup","status"]))
    return {"scope":"Private operational evidence — do not publish to GitHub","platform":platform.system(),"osVersion":command(["sw_vers","-productVersion"]),"architecture":platform.machine(),"memoryGiB":gib,"availableHomeGiB":round(shutil.disk_usage(Path.home()).free/1024**3,1),"fileVault":fv,"machineEncryptionGate":"requires_independent_verification" if fv=="on" else "blocked","operationalAccepted":False,"realClientAuthorised":False,"remaining":["Verify screen lock and named OS accounts","Verify local data directory and backup custody","Independent machine and human cohort acceptance","Approved retention, scanning, audit and calibration"]}
if __name__=="__main__":print(json.dumps(check(),indent=2))
