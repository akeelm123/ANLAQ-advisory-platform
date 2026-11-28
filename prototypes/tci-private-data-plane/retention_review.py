"""Offline explicit archive retention inventory; never deletes or restores records."""
import argparse,getpass,json,time
from pathlib import Path
from local_store import _derive,_private_file
from pilot_storage import inspect_synthetic_archive,LIMIT
from serve import REGISTER,SPEC
from data_plane import Invalid
def review(paths,salt_path,passphrase,clock=time.time):
    keys=_derive(passphrase,_private_file(Path(salt_path),32))
    return [{"archive":str(Path(p).name),**inspect_synthetic_archive(_private_file(Path(p),LIMIT+65536),*keys,REGISTER,SPEC,confirmed_synthetic=True,clock=clock)} for p in paths]
def main():
    p=argparse.ArgumentParser(description="Read-only synthetic archived-retention review")
    p.add_argument("--salt",required=True);p.add_argument("--archive",action="append",required=True);p.add_argument("--confirm-synthetic",action="store_true");a=p.parse_args()
    if not a.confirm_synthetic:p.error("Explicit fictional-only confirmation required")
    try:print(json.dumps({"scope":"private local inventory; no deletion","archives":review(a.archive,a.salt,getpass.getpass("Original vault passphrase: "))},indent=2))
    except (OSError,Invalid,ValueError):raise SystemExit("Archive inventory withheld: selected file, key, methodology or format could not be verified") from None
if __name__=="__main__":main()
