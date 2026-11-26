"""Run a local, throwaway synthetic end-to-end example. Never accepts client input."""
import secrets,tempfile,os
from pathlib import Path
from data_plane import DataPlane,Denied
root=Path(__file__).resolve().parent.parent.parent
register=Path(os.environ.get("TCI_REGISTER",root/"docs/tci/methodology/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"))
spec=Path(os.environ.get("TCI_SPEC",root/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
with tempfile.TemporaryDirectory() as tmp:
 dp=DataPlane(Path(tmp)/"demo.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),register,spec)
 try:
  a=dp.bootstrap_assessment("Synthetic tenant","Sample decision","Synthetic demo only")
  ts={}
  for role in ("contributor","assessor","reviewer","owner"):
   pw=secrets.token_urlsafe(24);u=dp.bootstrap_user(role,pw);dp.bootstrap_membership(a,u,role);ts[role]=dp.login(role,pw)
  v=dp.upload(ts["contributor"],a,"Synthetic mandate","mandate.txt",b"Synthetic strategy mandate and approved outcome")
  dp.inspect_quarantine(ts["assessor"],a,v["versionId"])
  dp.screen(ts["assessor"],a,v["versionId"],"accepted","Synthetic manual content screening")
  f=dp.draft_finding(ts["assessor"],a,"Q01","Synthetic strategy linkage finding","E1","Strong",False,[{"versionId":v["versionId"],"requestId":"SA-01","locator":"line 1"}])
  dp.review(ts["reviewer"],a,f,"accept","Synthetic independent review",True)
  print("Source version:",v["version"],"digest recorded:",bool(v["sha256"]))
  print("Review state:",dp.review_state(ts["owner"],a,f),"audit integrity:",dp.verify_audit())
  try:dp.release(ts["owner"],a)
  except Denied as e:print("Release blocked:",e)
 finally:dp.close()
