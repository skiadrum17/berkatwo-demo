from django.contrib import admin
from .models import Client, Package, Invoice, VendorTracker


class VendorTrackerInline(admin.TabularInline):
    """Inline untuk menampilkan VendorTracker di dalam Invoice."""
    model = VendorTracker
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'nama_lengkap', 'nomor_wa', 'email', 'created_at')
    search_fields = ('nama_lengkap', 'customer_id', 'nomor_wa', 'email')
    list_filter = ('created_at',)
    readonly_fields = ('customer_id', 'created_at')


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('nama_paket', 'harga_paket')
    search_fields = ('nama_paket',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'nomor_invoice', 'client', 'package', 'tanggal_dibuat',
        'total_tagihan', 'nominal_terbayar', 'sisa_tagihan', 'status',
    )
    list_filter = ('status', 'tanggal_dibuat')
    search_fields = ('nomor_invoice', 'client__nama_lengkap', 'client__customer_id')
    readonly_fields = ('nomor_invoice', 'sisa_tagihan')
    inlines = [VendorTrackerInline]
    list_editable = ('status', 'nominal_terbayar')


@admin.register(VendorTracker)
class VendorTrackerAdmin(admin.ModelAdmin):
    list_display = ('nama_vendor', 'invoice', 'status_pembayaran')
    list_filter = ('status_pembayaran',)
    search_fields = ('nama_vendor', 'invoice__nomor_invoice')
    list_editable = ('status_pembayaran',)
