# api/fetch.py
import os
import json
import requests
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

# Vercel Python runtime expects a handler-like object
def handler(request):
    """
    Vercel Python serverless function entry.
    Accepts query params:
      - category (optional)
      - q (optional search query)
      - page (optional)
    Returns JSON list of articles (newsdata.io format normalized).
    """
    # Read query params from request (Fast approach: use request.args if provided)
    params = {}
    try:
        qs = request.get('query', {})
        # request.get('query') when using Vercel's Python adapter returns dict of lists or strings.
        category = qs.get('category') or None
        q = qs.get('q') or None
        page = qs.get('page') or "1"
        params['category'] = category
        params['q'] = q
        params['page'] = page
    except Exception:
        category = None
        q = None
        page = "1"

    api_key = os.environ.get("NEWSDATA_API_KEY")
    if not api_key:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "NEWSDATA_API_KEY not set in environment"})
        }

    base = "https://newsdata.io/api/1/news"
    payload = {
        "apikey": api_key,
        "country": "in",
        "language": "en",
        "page": page
    }
    if category:
        payload["category"] = category
    if q:
        payload["q"] = q

    try:
        resp = requests.get(base, params=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Normalize results: ensure fields we use are present
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title"),
                "description": item.get("description"),
                "content": item.get("content"),
                "link": item.get("link") or item.get("url"),
                "image_url": item.get("image_url") or item.get("image"),
                "source": item.get("source_id") or item.get("source"),
                "author": item.get("creator") or item.get("author"),
                "pubDate": item.get("pubDate") or item.get("pubDate"),
            })
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True, "articles": results})
        }
    except requests.RequestException as e:
        return {
            "statusCode": 502,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "upstream error", "details": str(e)})
        }
