import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def search_arxiv(query, max_results=10, start_date=None, end_date=None, search_field=None):
    if not query or not isinstance(query, str) or query.strip() == "":
        raise ValueError("Query must be a non-empty string.")
    base_url = "http://export.arxiv.org/api/query"
    field_map = {"title": "ti", "author": "au", "summary": "abs"}
    if search_field and search_field in field_map:
        search_query = f'{field_map[search_field]}:"{query}"'
    else:
        search_query = query
    if start_date or end_date:
        date_query = []
        if start_date:
            date_query.append(f"submittedDate:[{start_date}0000 TO")
        else:
            date_query.append("submittedDate:[* TO")
        if end_date:
            date_query[-1] += f" {end_date}2359]"
        else:
            date_query[-1] += " *]"
        search_query = f"{search_query} AND {''.join(date_query)}"
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results
    }
    try:
        resp = requests.get(base_url, params=params, timeout=10)
    except requests.RequestException:
        raise ConnectionError("Network error occurred.")
    if resp.status_code == 429:
        raise Exception("Rate limit exceeded.")
    if resp.status_code != 200:
        raise ValueError(f"arXiv API error: {resp.status_code}")
    try:
        root = ET.fromstring(resp.text)
    except Exception:
        raise ValueError("Invalid API response format.")
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entries = root.findall('atom:entry', ns)
    results = []
    for entry in entries:
        try:
            title = entry.find('atom:title', ns).text.strip()
            authors = [a.find('atom:name', ns).text.strip() for a in entry.findall('atom:author', ns)]
            summary = entry.find('atom:summary', ns).text.strip()
            pdf_url = None
            for link in entry.findall('atom:link', ns):
                if link.attrib.get('type') == 'application/pdf':
                    pdf_url = link.attrib.get('href')
                    break
            if not pdf_url:
                pdf_url = entry.find('atom:id', ns).text.replace('abs', 'pdf') + '.pdf'
            results.append({
                "title": title,
                "authors": authors,
                "summary": summary,
                "pdf_url": pdf_url
            })
        except Exception:
            continue
    return results
