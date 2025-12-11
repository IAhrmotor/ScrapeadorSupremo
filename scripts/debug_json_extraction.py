"""Debug JSON extraction from Cochesnet HTML."""

import re
import json

# Read HTML
with open('cochesnet_debug.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Try to find the JSON
pattern = r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\((.*?)\);'
match = re.search(pattern, html, re.DOTALL)

if match:
    print("Found match!")
    raw = match.group(1)
    print(f"Length: {len(raw)}")
    print(f"First 500 chars: {raw[:500]}")
    print(f"\nLast 500 chars: {raw[-500:]}")

    # Try to parse
    try:
        # Remove outer quotes if present
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]

        # Decode unicode escapes
        decoded = raw.encode().decode('unicode_escape')
        print(f"\nDecoded first 500: {decoded[:500]}")

        # Parse JSON
        data = json.loads(decoded)
        print(f"\nJSON parsed successfully!")
        print(f"Keys: {list(data.keys())[:10]}")

        # Look for items
        if 'initialResults' in data:
            items = data['initialResults'].get('items', [])
            print(f"\nFound {len(items)} items in data['initialResults']")
        elif 'props' in data:
            page_props = data['props'].get('pageProps', {})
            if 'initialResults' in page_props:
                items = page_props['initialResults'].get('items', [])
                print(f"\nFound {len(items)} items in data['props']['pageProps']['initialResults']")
            else:
                print(f"\nNo initialResults in pageProps")
                print(f"pageProps keys: {list(page_props.keys())}")
        else:
            print(f"\nNo 'initialResults' or 'props' in data")
            print(f"Top-level keys: {list(data.keys())}")

    except Exception as e:
        print(f"\nError parsing: {e}")
        import traceback
        traceback.print_exc()

else:
    print("No match found with pattern!")
    print("Trying alternative pattern...")

    # Try without requiring semicolon
    pattern2 = r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\("([^"]+)"\)'
    match2 = re.search(pattern2, html)

    if match2:
        print("Found with alternative pattern!")
        print(f"Length: {len(match2.group(1))}")
    else:
        print("Still no match. Showing first occurrence:")
        idx = html.find('window.__INITIAL_PROPS__')
        if idx >= 0:
            print(html[idx:idx+500])
