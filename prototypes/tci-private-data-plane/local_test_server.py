"""Internal synthetic test harness. Credentials supplied only over process stdin."""
import json,signal,sys
from local_store import LocalStore
from local_pilot import make_server
from serve import REGISTER,SPEC

def main():
    cfg=json.loads(sys.stdin.readline())
    def stop(*_):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    with LocalStore(cfg["directory"],REGISTER,SPEC) as s:
        if cfg["initialize"]:s.initialize(cfg["passphrase"],cfg["accounts"])
        else:s.unlock(cfg["passphrase"])
        if cfg.get("simulateCheckpointFailure"):
            def fail():raise OSError("Synthetic checkpoint test failure")
            s.checkpoint=fail
        with make_server(s,0) as server:
            aid=s.dp.db.execute("SELECT id FROM assessments").fetchone()[0]
            print(json.dumps({"url":"http://127.0.0.1:"+str(server.server_port),"assessment":aid}),flush=True)
            try:server.serve_forever()
            except KeyboardInterrupt:pass
if __name__=="__main__":main()
