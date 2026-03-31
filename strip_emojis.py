import re
import os

known_emojis = ['📊', '📈', '🗺️', '🔑', '📥', '💧', '🌐', '🛡️', '❌', 'ℹ️', '⚠️', '✅', '🧪', '👥', '⚙️', '🔍', '⚙', '🚀', '📝', '🔗', '📍', '📉', '📂', '💡', '📌']

for file in os.listdir('.'):
    if file.endswith('.py') and file != 'strip_emojis.py':
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        cleaned = content
        for e in known_emojis:
            cleaned = cleaned.replace(e, '')
            # also replace if there's a space after the emoji (like "📥 Download" -> " Download" -> "Download")
            cleaned = cleaned.replace(e + ' ', '')
            
        if cleaned != content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(cleaned)

print("Done stripping.")
