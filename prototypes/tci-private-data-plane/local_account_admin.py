"""Offline named-account maintenance for synthetic local vaults, never remote access."""
import argparse,getpass
from local_store import LocalStore
from serve import REGISTER,SPEC
from data_plane import Denied,Invalid,password_hash,required
import hmac,secrets

def rotate_member_password(dp,token,aid,username,new_password,reason,confirmed=False):
    if confirmed is not True or not isinstance(new_password,str) or not 12<=len(new_password)<=256:raise Invalid("Explicit rotation and unique password required")
    with dp.db:
        actor=dp._actor(token,aid,{"owner"})
        row=dp.db.execute("SELECT u.id FROM users u JOIN membership m ON m.user_id=u.id WHERE m.assessment_id=? AND u.username=? AND u.active=1 AND m.active=1",(aid,username)).fetchone()
        if not row:raise Denied("Active named membership required")
        for u in dp.db.execute("SELECT salt,password FROM users"):
            if hmac.compare_digest(password_hash(new_password,u["salt"]),u["password"]):raise Invalid("Password must differ from existing named-account passwords")
        required(reason,"rotation rationale");salt=secrets.token_bytes(16)
        dp.db.execute("UPDATE users SET salt=?,password=? WHERE id=?",(salt,password_hash(new_password,salt),row["id"]))
        dp.db.execute("DELETE FROM sessions WHERE user_id=?",(row["id"],))
        dp._audit(aid,actor["id"],"named account credential rotated; sessions revoked",row["id"])

def main():
    p=argparse.ArgumentParser(description="Offline synthetic local account credential maintenance")
    p.add_argument("--data-dir",required=True);p.add_argument("--member",required=True);p.add_argument("--confirm-synthetic",action="store_true");a=p.parse_args()
    if not a.confirm_synthetic:p.error("Explicit fictional-only scope required")
    try:
      with LocalStore(a.data_dir,REGISTER,SPEC) as s:
        dp=s.unlock(getpass.getpass("Vault passphrase: "))
        owner=dp.login(input("Owner username: ").strip(),getpass.getpass("Owner password: "))
        memberships=[x for x in dp.list_assessments(owner) if x["role"]=="owner"]
        if len(memberships)!=1:raise Invalid("Exactly one authorised owner assessment required for this local tool")
        pw=getpass.getpass("New member password: ");repeat=getpass.getpass("Confirm new password: ")
        if pw!=repeat:raise Invalid("Confirmation mismatch")
        reason=input("Reason for rotation: ");confirmed=input("Type yes to rotate this named account and revoke its sessions: ")=="yes"
        rotate_member_password(dp,owner,memberships[0]["id"],a.member,pw,reason,confirmed);s.checkpoint()
        print("Named account credential rotated and checkpoint saved; restart requires new sign-in.")
    except (Invalid,Denied,OSError):raise SystemExit("Account maintenance refused; no successful rotation confirmed") from None
if __name__=="__main__":main()
