import os
import re

files = [
    'templates/dashboard.html',
    'templates/invoice_list.html',
    'templates/edit_info.html',
    'templates/admin_invoice.html',
    'templates/create_invoice.html'
]

replacement = '''
                <div class="flex items-center gap-3 pl-4 border-l border-gray-200 dark:border-dark-50/30">
                    <div class="w-9 h-9 rounded-full bg-gold-500 flex items-center justify-center text-dark-900 font-bold text-xs">
                        {% if request.user.first_name %}{{ request.user.first_name|make_list|first|upper }}{% else %}{{ request.user.username|make_list|first|upper }}{% endif %}
                    </div>
                    <div class="hidden md:block overflow-hidden max-w-[150px]">
                        <p class="text-sm text-gray-900 dark:text-white font-medium truncate">{% if request.user.first_name %}{{ request.user.first_name }} {{ request.user.last_name }}{% else %}{{ request.user.username }}{% endif %}</p>
                        <p class="text-[10px] text-gray-600 dark:text-gray-500">Administrator</p>
                    </div>
                </div>
'''

search_pattern = re.compile(
    r'<div class="flex items-center gap-3 pl-4 border-l border-gray-200 dark:border-dark-50/30">.*?<div class="w-9 h-9 rounded-full bg-gold-500 flex items-center justify-center text-dark-900 font-bold text-xs">AU</div>.*?<div class="hidden md:block">.*?<p class="text-sm text-gray-900 dark:text-white font-medium">Admin User</p>.*?<p class="text-\[10px\] text-gray-600 dark:text-gray-500">Administrator</p>.*?</div>.*?</div>',
    re.DOTALL
)

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = search_pattern.sub(replacement.strip(), content)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(new_content)
