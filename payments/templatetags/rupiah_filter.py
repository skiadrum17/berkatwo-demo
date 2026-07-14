from django import template
import locale

register = template.Library()


@register.filter(name='rupiah')
def rupiah(value):
    """Format angka ke format Rupiah dengan titik sebagai pemisah ribuan.
    
    Contoh: 150000000 → 'Rp 150.000.000'
    """
    try:
        value = int(value)
        formatted = f'{value:,.0f}'.replace(',', '.')
        return f'Rp {formatted}'
    except (ValueError, TypeError):
        return 'Rp 0'


@register.filter(name='rupiah_plain')
def rupiah_plain(value):
    """Format angka dengan titik sebagai pemisah ribuan tanpa prefix Rp.
    
    Contoh: 150000000 → '150.000.000'
    """
    try:
        value = int(value)
        return f'{value:,.0f}'.replace(',', '.')
    except (ValueError, TypeError):
        return '0'
