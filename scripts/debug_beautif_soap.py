"""Debug how BeautifulSoup parses the script tag."""

from bs4 import BeautifulSoup
import re

# Read HTML
with open('cochesnet_debug.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')
scripts = soup.find_all('script')

print(f"Total scripts found: {len(scripts)}")

found_initial_props = 0
for i, script in enumerate(scripts):
    text = script.string
    if not text:
        continue

    if '__INITIAL_PROPS__' in text:
        found_initial_props += 1
        print(f"\nScript #{i+1} contains __INITIAL_PROPS__")
        print(f"Text length: {len(text)}")
        print(f"First 200 chars: {text[:200]}")

        # Try the regex from parser
        pattern = r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\("(.+?)"\)'
        match = re.search(pattern, text, re.DOTALL)

        print(f"Regex match: {match is not None}")

        if match:
            print(f"Match group 1 length: {len(match.group(1))}")
        else:
            # Try to see why it doesn't match
            print("Trying to find why it doesn't match...")

            # Check if pattern exists at all
            if 'JSON.parse(' in text:
                idx = text.find('JSON.parse(')
                print(f"JSON.parse found at position {idx}")
                print(f"Context: {text[idx:idx+100]}")
            else:
                print("JSON.parse NOT found in text")

print(f"\nTotal scripts with __INITIAL_PROPS__: {found_initial_props}")
