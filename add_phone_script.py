import os
import re

files = [
    'templates/create_invoice.html',
    'templates/admin_invoice.html',
    'templates/edit_info.html'
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = re.sub(
        r'(<input[^>]+name="(?:nomor_wa|wa_number|nomor_wa_konfirmasi)"[^>]+class=")([^"]+)(")',
        r'\g<1>phone-input \g<2>\g<3>',
        content
    )
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

with open('templates/base.html', 'r', encoding='utf-8') as f:
    base_content = f.read()

script = '''
    <script>
        // Phone number formatting
        document.addEventListener('input', function(e) {
            if (e.target.classList.contains('phone-input')) {
                let val = e.target.value.replace(/\D/g, '');
                let formatted = '';
                for (let i = 0; i < val.length; i++) {
                    if (i > 0 && i % 4 === 0) {
                        formatted += '-';
                    }
                    formatted += val[i];
                }
                e.target.value = formatted;
            }
        });
    </script>
'''

if 'phone-input' not in base_content:
    base_content = base_content.replace('{% block extra_scripts %}{% endblock %}', script + '\n    {% block extra_scripts %}{% endblock %}')
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base_content)
