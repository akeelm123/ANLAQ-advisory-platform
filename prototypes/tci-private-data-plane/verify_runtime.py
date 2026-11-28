"""Verify tested direct/transitive runtime versions, not a vulnerability scan."""
import importlib.metadata,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def verify():
    expected={}
    for line in (HERE/"requirements-tested-lock.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):continue
        name,value=line.split("==");expected[name]=value
    results=[]
    for name,value in expected.items():
        try:actual=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:actual=None
        results.append({"package":name,"expected":value,"actual":actual,"matches":actual==value})
    return {"python":f"{sys.version_info.major}.{sys.version_info.minor}","packages":results,"matchesTestedRuntime":sys.version_info[:2]==(3,12) and all(x["matches"] for x in results),"securityAssurance":False}
if __name__=="__main__":print(json.dumps(verify(),indent=2))
