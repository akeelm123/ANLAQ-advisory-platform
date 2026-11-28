"""Conservative review flags for comparable-looking fictional documentary signals."""
import re
from evidence_matching import NUM,terms
PERIOD=re.compile(r"\b(?:FY\s*\d{2,4}|20\d{2}|Q[1-4]|Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b",re.I)
ACTUAL=re.compile(r"\b(actual|measured|observed|recorded|reported|active|usage|availability|throughput|cycle time|defect|rework|incident|result)\b",re.I)
FORECAST=re.compile(r"\b(forecast|projected|target|planned|expected)\b",re.I)
def numeric_mentions(text):
    for m in NUM.finditer(text):
        unit=m[2].casefold().rstrip("s").replace("percent","%")
        context=terms(text[max(0,m.start()-70):m.end()+45])
        yield unit,m[1],context
def documentary_flags(sources):
    out=set()
    for i,a in enumerate(sources):
        for b in sources[i+1:]:
            if a.get("digest")==b.get("digest"):continue
            x,y=a["quote"],b["quote"];pa={m.group().lower() for m in PERIOD.finditer(x)};pb={m.group().lower() for m in PERIOD.finditer(y)}
            # Only compare documents with explicit, matching period sets and actual-looking measures.
            if not pa or pa!=pb or not ACTUAL.search(x) or not ACTUAL.search(y) or FORECAST.search(x) or FORECAST.search(y):continue
            if any(u==v and n!=m and len({w for w in cx&cy if not w.startswith("concept")})>=3 for u,n,cx in numeric_mentions(x) for v,m,cy in numeric_mentions(y)):out.add("document_numeric_discrepancy_review")
    return sorted(out)
def operating_context(sources):
    text=" ".join(x.get("quote","") for x in sources)
    if not ACTUAL.search(text):return False
    quarters={m.group().upper() for m in re.finditer(r"\bQ[1-4]\b",text,re.I)}
    years={m.group().upper() for m in re.finditer(r"\b(?:FY\s*\d{2,4}|20\d{2})\b",text,re.I)}
    dates={m.group().casefold() for m in re.finditer(r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+20\d{2}\b",text,re.I)}
    return len(quarters)>=2 or len(years)>=2 or len(dates)>=2 or bool(re.search(r"\b(?:over|across|for)\s+(?:\d+|two|three|four|six|multiple|several)\s+(?:months|quarters|years|reporting periods)\b",text,re.I))
