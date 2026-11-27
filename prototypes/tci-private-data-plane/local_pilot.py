"""Persistent, synthetic-only loopback launcher; never exposes a LAN/public listener."""
import argparse,getpass,json,signal,webbrowser
from pathlib import Path
from http.server import HTTPServer
from data_plane import Denied,Invalid
from local_store import LocalStore,ROLES
from serve import Handler,REGISTER,SPEC

class PersistentHandler(Handler):
    def execute(self,method):
        if self.server.failed:return super().payload(503,{"error":"Local storage unavailable; restart and verify last saved state"})
        return super().execute(method)
    def payload(self,status,data):
        # Success is not acknowledged until the encrypted database checkpoint is durable.
        if self.command=="POST" and 200<=status<300 and self.path not in ("/api/login","/api/logout"):
            try:self.server.store.checkpoint()
            except Exception:
                self.server.failed=True
                return super().payload(503,{"error":"Local checkpoint failed; stop and inspect last saved state"})
        return super().payload(status,data)

def make_server(store,port):
    server=HTTPServer(("127.0.0.1",port),PersistentHandler)
    server.dp=store.dp;server.store=store;server.failed=False;server.local_persistent=True
    server.aurora_summary=None;server.aurora_assessment=None
    return server

def prompt_secret(label,min_length=12):
    v=getpass.getpass(label+": ");confirm=getpass.getpass("Confirm "+label.lower()+": ")
    if v!=confirm or len(v)<min_length:raise Invalid("Confirmation mismatch or secret too short")
    return v

def main():
    p=argparse.ArgumentParser(description="Synthetic-only persistent local TCI pilot")
    p.add_argument("--data-dir",default=str(Path.home()/"Library/Application Support/ANLAQ-TCI-Synthetic"))
    p.add_argument("--port",type=int,default=8765);p.add_argument("--initialize",action="store_true");p.add_argument("--open-browser",action="store_true")
    p.add_argument("--confirm-synthetic",action="store_true",help="Confirm fictional records only; no real-client processing")
    p.add_argument("--backup",help="Create a new encrypted archive at an explicit local path; no overwrite")
    p.add_argument("--restore-backup",help="Recover an encrypted archive into a NEW empty vault");p.add_argument("--restore-salt",help="Original vault salt file for recovery")
    a=p.parse_args()
    if bool(a.restore_backup)!=bool(a.restore_salt) or (a.initialize and a.restore_backup):p.error("Choose initialization or restore with both archive and salt")
    if not a.confirm_synthetic:p.error("Explicit --confirm-synthetic required; no real-client processing")
    def stop(*_):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    try:
      with LocalStore(a.data_dir,REGISTER,SPEC) as store:
        if a.initialize:
          passphrase=prompt_secret("New vault passphrase",16);accounts={}
          for role in ROLES:
            name=input("Named "+role+" username: ").strip();pw=prompt_secret("Password for "+role)
            accounts[role]=(name,pw)
          store.initialize(passphrase,accounts);del accounts
        elif a.restore_backup:
          passphrase=getpass.getpass("Original vault passphrase: ");store.recover_backup(a.restore_backup,a.restore_salt,passphrase)
        else:passphrase=getpass.getpass("Vault passphrase: ");store.unlock(passphrase)
        del passphrase
        if a.backup:
          store.backup(a.backup);print("Encrypted backup created. Keep the vault salt separately with approved backup custody.");return
        with make_server(store,a.port) as server:
          url="http://127.0.0.1:"+str(server.server_port)
          print("Synthetic local pilot is available at "+url+"; sign in with your named account. Keep this window open.",flush=True)
          if a.open_browser:webbrowser.open(url)
          try:server.serve_forever()
          except KeyboardInterrupt:pass
    except (Invalid,OSError,ValueError) as e:raise SystemExit("Local pilot not started: "+str(e)) from None
if __name__=="__main__":main()
