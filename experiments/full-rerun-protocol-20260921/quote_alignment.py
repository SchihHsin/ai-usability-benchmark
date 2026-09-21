"""Locate plain-text quotations in captured Markdown without changing wording."""
import re

def projected(text):
    hidden=set()
    for m in re.finditer(r'\[([^\]\n]+)\]\(([^\n]*?)\)',text):
        hidden.add(m.start());hidden.update(range(m.start(1)+len(m.group(1)),m.end()))
    for m in re.finditer(r'`+|\*\*|__',text):hidden.update(range(m.start(),m.end()))
    chars=[];positions=[]
    for i,ch in enumerate(text):
        if i not in hidden:chars.append(ch);positions.append(i)
    return ''.join(chars),positions

def align(quote,source):
    plain,mapping=projected(source);q,_=projected(quote)
    if len(q.strip())<20 or plain.count(q)!=1:return None
    start=plain.index(q);end=start+len(q)
    candidate=source[mapping[start]:mapping[end-1]+1]
    # Mapping may end before a closing Markdown delimiter; retain full original
    # span only as evidence, with every lexical character still unchanged.
    return candidate if candidate in source else None
