import os
import re

files = [
    'templates/dashboard.html',
    'templates/invoice_list.html',
    'templates/edit_info.html',
    'templates/admin_invoice.html',
    'templates/create_invoice.html'
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = re.sub(r'\s*style="animation-delay:\s*[\d\.]+s"', '', content)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
