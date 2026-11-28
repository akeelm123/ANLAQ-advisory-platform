"""Content-based catalogue suggestions; no automatic declaration or score."""
import math
from evidence_matching import terms
def normal_terms(text):
    out=set()
    for w in terms(text):
        if w.startswith("concept"):out.add(w);continue
        if len(w)>4 and w.endswith("ies"):w=w[:-3]+"y"
        elif len(w)>4 and w.endswith("s") and not w.endswith("ss"):w=w[:-1]
        if len(w)>6 and w.endswith("ing"):w=w[:-3]
        if len(w)>5 and w.endswith("ed"):w=w[:-2]
        out.add(w)
    return out
def build_index(catalogue,rules):
    index={}
    for item in catalogue.values():
        linked=[r for r in rules.values() if item["id"] in r["primary"]]
        related=[r for r in rules.values() if item["id"] in r["supplementary"]]
        index[item["id"]]=(normal_terms(item["title"]),normal_terms(item["extract"]),normal_terms(item["purpose"]+" "+item["alternative"]),normal_terms(" ".join(r["criterion"]+" "+r["fields"]+" "+r["test"] for r in linked)),normal_terms(" ".join(r["criterion"]+" "+r["fields"] for r in related)))
    allterms=set.union(*(set.union(*v) for v in index.values()))
    idf={w:math.log(1+len(index)/sum(w in set.union(*v) for v in index.values())) for w in allterms}
    return index,idf
def suggest_categories(catalogue,segments,index,limit=3):
    fields,idf=index;indexed=[(s,normal_terms(s["text"])) for s in segments]
    if not indexed:return []
    document=set.union(*(t for _,t in indexed));out=[]
    for key,groups in fields.items():
        seen=set();rank=0
        for weight,group in zip((2,2,1,.4,.1),groups):
            match=(group&document)-seen;seen|=match;rank+=weight*sum(idf[w] for w in match)
        ordinary={w for w in seen if not w.startswith("concept")}
        if len(ordinary)<3 or rank<9:continue
        s,t=max(indexed,key=lambda item:(sum(idf[w] for w in item[1]&seen),item[0]["location"]))
        out.append({"id":key,"title":catalogue[key]["title"],"rank":round(rank,2),"locator":s["location"],"matchedTerms":sorted((t&ordinary))[:12],"status":"candidate"})
    return sorted(out,key=lambda x:(-x["rank"],x["id"]))[:limit]
