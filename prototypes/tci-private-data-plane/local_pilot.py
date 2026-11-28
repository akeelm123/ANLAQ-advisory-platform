"""Persistent, synthetic-only loopback launcher; never exposes a LAN/public listener."""
import argparse,errno,getpass,json,signal,webbrowser
from pathlib import Path
from http.server import HTTPServer
from data_plane import Denied,Invalid
from local_store import LocalStore,ROLES
from serve import Handler,REGISTER,SPEC
from document_parser import enable_child_parser

class PersistentHandler(Handler):
    def execute(self,method):
        if self.server.failed:return super().payload(503,{"error":"Local storage unavailable; restart and verify last saved state"})
        return super().execute(method)
    def payload(self,status,data):
        # Success is not acknowledged until the encrypted database checkpoint is durable.
        if self.command=="POST" and (200<=status<300 or (status==400 and self.path.endswith("/upload"))) and self.path not in ("/api/login","/api/logout"):
            try:self.server.store.checkpoint()
            except Exception:
                self.server.failed=True
                return super().payload(503,{"error":"Local checkpoint failed; stop and inspect last saved state"})
        return super().payload(status,data)

def make_server(store,port,auto_port=False,require_scan=False,child_parser=True):
    try:server=HTTPServer(("127.0.0.1",port),PersistentHandler)
    except OSError as e:
        if not auto_port or e.errno!=errno.EADDRINUSE:raise
        server=HTTPServer(("127.0.0.1",0),PersistentHandler)
    enable_child_parser(child_parser);store.dp.intake_assurance.require_scan=require_scan
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
    p.add_argument("--port",type=int,default=8765);p.add_argument("--auto-port",action="store_true",help="Choose an unused loopback port if requested port is occupied");p.add_argument("--initialize",action="store_true");p.add_argument("--open-browser",action="store_true")
    p.add_argument("--require-malware-scan",action="store_true",help="Fail closed on upload if installed ClamAV cannot give a clean result");p.add_argument("--confirm-synthetic",action="store_true",help="Confirm fictional records only; no real-client processing")
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
        with make_server(store,a.port,auto_port=a.auto_port,require_scan=a.require_malware_scan) as server:
          url="http://127.0.0.1:"+str(server.server_port)
          if a.port and server.server_port!=a.port:print("Requested port is occupied; using a different local port. No existing server was stopped.",flush=True)
          print("Synthetic local pilot is available at "+url+"; sign in with your named account. Keep this window open.",flush=True)
          if a.open_browser:webbrowser.open(url)
          try:server.serve_forever()
          except KeyboardInterrupt:pass
    except (Invalid,OSError,ValueError) as e:raise SystemExit("Local pilot not started: "+str(e)) from None
if __name__=="__main__":main()
