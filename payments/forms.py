from django import forms
from django.contrib.auth.models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind CSS classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-dark-50/20 bg-white dark:bg-dark-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-gold-500/50 focus:border-gold-500 outline-none transition-all placeholder-gray-400'
            
            # Additional placeholders or specific configurations
            if field_name == 'first_name':
                field.widget.attrs['placeholder'] = 'Nama Depan'
            elif field_name == 'last_name':
                field.widget.attrs['placeholder'] = 'Nama Belakang'
            elif field_name == 'username':
                field.widget.attrs['placeholder'] = 'Username (Wajib)'
            elif field_name == 'email':
                field.widget.attrs['placeholder'] = 'Email'
