from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Q
from django.contrib import messages
from .models import Client, Package, Invoice, VendorTracker, BusinessSettings


def dashboard_view(request):
    """Dashboard admin — metrik keseluruhan dan daftar 5 invoice terbaru."""
    invoices = Invoice.objects.select_related('client', 'package').all()

    # Aggregate metrics
    metrics = invoices.aggregate(
        total_invoiced=Sum('total_tagihan'),
        total_received=Sum('nominal_terbayar'),
        outstanding=Sum('sisa_tagihan'),
    )

    total_invoiced = metrics['total_invoiced'] or 0
    total_received = metrics['total_received'] or 0
    outstanding = metrics['outstanding'] or 0

    # Count overdue
    overdue_count = invoices.filter(status='overdue').count()
    overdue_amount = invoices.filter(status='overdue').aggregate(
        total=Sum('sisa_tagihan')
    )['total'] or 0

    # Active invoice count
    active_count = Invoice.objects.exclude(status='lunas').count()

    # Only pass the 5 most recent invoices to dashboard
    recent_invoices = invoices[:5]

    context = {
        'invoices': recent_invoices,
        'total_invoiced': total_invoiced,
        'total_received': total_received,
        'outstanding': outstanding,
        'overdue_count': overdue_count,
        'overdue_amount': overdue_amount,
        'active_count': active_count,
    }
    return render(request, 'dashboard.html', context)


def invoice_list_view(request):
    """View khusus untuk menampilkan seluruh invoice dengan filter dan pencarian."""
    invoices = Invoice.objects.select_related('client', 'package').all()

    # Filter by tab
    tab = request.GET.get('tab', 'all')
    if tab == 'pending':
        invoices = invoices.filter(status__in=['menunggu', 'dp', 'proses'])
    elif tab == 'lunas':
        invoices = invoices.filter(status='lunas')
    elif tab == 'overdue':
        invoices = invoices.filter(status='overdue')

    # Search
    search = request.GET.get('q', '')
    if search:
        invoices = invoices.filter(
            Q(client__nama_lengkap__icontains=search) |
            Q(nomor_invoice__icontains=search) |
            Q(client__customer_id__icontains=search)
        )

    context = {
        'invoices': invoices,
        'current_tab': tab,
        'search_query': search,
    }
    return render(request, 'invoice_list.html', context)


def delete_invoice_view(request, nomor_invoice):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, nomor_invoice=nomor_invoice)
        invoice.delete()
        messages.success(request, f'Invoice {nomor_invoice} berhasil dihapus.')
    return redirect('invoice_list')


def admin_invoice_view(request, nomor_invoice):
    """Admin invoice detail — untuk CRUD invoice oleh admin.
    
    Admin bisa:
    - Mengubah status pembayaran invoice
    - Mengubah nominal_terbayar (uang yang sudah dibayar klien)
    - Mengelola vendor monitoring (harga vendor, nominal dibayar ke vendor, status)
    """
    invoice = get_object_or_404(
        Invoice.objects.select_related('client', 'package'),
        nomor_invoice=nomor_invoice,
    )
    vendors = invoice.vendors.all()
    settings = BusinessSettings.get_solo()

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_settings':
            settings.nama_bisnis = request.POST.get('nama_bisnis', settings.nama_bisnis)
            settings.email_bisnis = request.POST.get('email_bisnis', settings.email_bisnis)
            settings.lokasi = request.POST.get('lokasi', settings.lokasi)
            settings.terms_and_conditions = request.POST.get('terms_and_conditions', settings.terms_and_conditions)
            settings.nama_bank = request.POST.get('nama_bank', settings.nama_bank)
            settings.nomor_rekening = request.POST.get('nomor_rekening', settings.nomor_rekening)
            settings.atas_nama_rekening = request.POST.get('atas_nama_rekening', settings.atas_nama_rekening)
            settings.nomor_wa_konfirmasi = request.POST.get('nomor_wa_konfirmasi', settings.nomor_wa_konfirmasi)
            settings.save()
            messages.success(request, 'Pengaturan bisnis berhasil diperbarui.')

        if action == 'update_invoice':
            # Update status & nominal terbayar
            new_status = request.POST.get('status', invoice.status)
            new_terbayar = request.POST.get('nominal_terbayar', 0)
            request_client = request.POST.get('request_client', invoice.request_client)
            try:
                new_terbayar = int(new_terbayar)
            except (ValueError, TypeError):
                new_terbayar = invoice.nominal_terbayar

            invoice.status = new_status
            invoice.nominal_terbayar = new_terbayar
            invoice.request_client = request_client
            invoice.save()
            messages.success(request, 'Invoice berhasil diperbarui.')

        elif action == 'update_vendors':
            # Update each vendor
            for vendor in vendors:
                progress_key = f'progress_persen_{vendor.id}'
                status_key = f'status_vendor_{vendor.id}'

                progress = request.POST.get(progress_key, vendor.progress_persen)
                status = request.POST.get(status_key, vendor.status_pembayaran)

                try:
                    vendor.progress_persen = max(0, min(100, int(progress)))
                except (ValueError, TypeError):
                    pass

                vendor.status_pembayaran = status
                vendor.save()

            messages.success(request, 'Data vendor berhasil diperbarui.')

        elif action == 'add_vendor':
            nama = request.POST.get('new_vendor_nama', '').strip()
            if nama:
                VendorTracker.objects.create(
                    invoice=invoice,
                    nama_vendor=nama,
                )
                messages.success(request, f'Vendor "{nama}" berhasil ditambahkan.')

        elif action == 'delete_vendor':
            vendor_id = request.POST.get('vendor_id')
            if vendor_id:
                VendorTracker.objects.filter(id=vendor_id, invoice=invoice).delete()
                messages.success(request, 'Vendor berhasil dihapus.')

        return redirect('admin_invoice', nomor_invoice=nomor_invoice)

    import urllib.parse
    from django.urls import reverse
    
    # Generate WhatsApp Link for Client
    client_phone = invoice.client.nomor_wa
    if client_phone.startswith('0'):
        client_phone = '62' + client_phone[1:]
        
    portal_link = request.build_absolute_uri(reverse('client_portal', args=[invoice.nomor_invoice]))
    
    wa_message = f"""Selamat pagi/siang/sore kak {invoice.client.nama_lengkap}. :)

Terima kasih, kami telah menerima pembayaran dari Bapak/Ibu untuk layanan Berkat Wedding Organizer.

Sebagai bukti administrasi, kami lampirkan Invoice Pembayaran yang telah kami update sesuai dengan transaksi yang diterima.
Bapak/Ibu dapat melihat dan mengunduh Invoice melalui link berikut:
{portal_link}

Kami sangat menghargai kepercayaan Bapak/Ibu kepada Berkat Wedding Organizer. Selanjutnya, tim kami akan terus melakukan persiapan dan koordinasi untuk memastikan setiap rangkaian acara berjalan dengan baik.

Apabila terdapat pertanyaan atau membutuhkan informasi lebih lanjut, kami dengan senang hati siap membantu.

Terima kasih atas kepercayaan dan kerja samanya.

Salam hangat,
Admin Berkat WO"""
    
    wa_client_link = f"https://wa.me/{client_phone}?text={urllib.parse.quote(wa_message)}"

    context = {
        'invoice': invoice,
        'client': invoice.client,
        'package': invoice.package,
        'vendors': vendors,
        'status_choices': Invoice.STATUS_CHOICES,
        'vendor_status_choices': VendorTracker.STATUS_CHOICES,
        'wa_client_link': wa_client_link,
        'settings': settings,
    }
    return render(request, 'admin_invoice.html', context)


def print_invoice_view(request, nomor_invoice):
    """View untuk mencetak invoice ke PDF via print window browser."""
    invoice = get_object_or_404(
        Invoice.objects.select_related('client', 'package'),
        nomor_invoice=nomor_invoice,
    )
    settings = BusinessSettings.get_solo()
    
    terms_list = [t.strip() for t in settings.terms_and_conditions.split('\n') if t.strip()]
    
    context = {
        'invoice': invoice,
        'client': invoice.client,
        'package': invoice.package,
        'settings': settings,
        'terms_list': terms_list,
    }
    return render(request, 'print_invoice.html', context)


def client_portal_view(request, nomor_invoice):
    """Client portal — detail invoice spesifik untuk klien (read-only)."""
    try:
        invoice = Invoice.objects.select_related('client', 'package').get(nomor_invoice=nomor_invoice)
    except Invoice.DoesNotExist:
        return render(request, 'invoice_not_found.html', {'nomor_invoice': nomor_invoice}, status=404)
    vendors = invoice.vendors.all()
    settings = BusinessSettings.get_solo()

    # WhatsApp message template
    wa_number = invoice.wa_number or settings.nomor_wa_konfirmasi
    wa_message = (
        f'Halo {settings.nama_bisnis}, saya {invoice.client.nama_lengkap} '
        f'ingin konfirmasi pembayaran untuk invoice {invoice.nomor_invoice}. '
        f'Terima kasih.'
    )
    wa_link = f'https://api.whatsapp.com/send?phone={wa_number}&text={wa_message}'

    context = {
        'invoice': invoice,
        'client': invoice.client,
        'package': invoice.package,
        'vendors': vendors,
        'wa_link': wa_link,
        'wa_number': wa_number,
        'settings': settings,
    }
    return render(request, 'client_portal.html', context)


def create_invoice_view(request):
    """View untuk membuat invoice baru."""
    if request.method == 'POST':
        # Get or create client
        nama_lengkap = request.POST.get('nama_lengkap', '')
        nomor_wa = request.POST.get('nomor_wa', '')
        email = request.POST.get('email', '')

        client, created = Client.objects.get_or_create(
            nama_lengkap=nama_lengkap,
            nomor_wa=nomor_wa,
            defaults={'email': email},
        )

        # Get package
        package_id = request.POST.get('package_id')
        package = None
        if package_id:
            package = Package.objects.filter(id=package_id).first()

        # Get custom bank info if available
        bank_name = request.POST.get('bank_name', '')
        bank_account = request.POST.get('bank_account', '')
        bank_account_name = request.POST.get('bank_account_name', '')
        wa_number = request.POST.get('wa_number', '')

        # Create invoice
        total_tagihan = request.POST.get('total_tagihan', 0)
        try:
            total_tagihan = int(total_tagihan)
        except (ValueError, TypeError):
            total_tagihan = 0

        invoice = Invoice.objects.create(
            client=client,
            package=package,
            total_tagihan=total_tagihan,
            bank_name=bank_name,
            bank_account=bank_account,
            bank_account_name=bank_account_name,
            wa_number=wa_number,
            request_client=request.POST.get('request_client', ''),
        )
        
        tanggal_dibuat = request.POST.get('tanggal_dibuat')
        if tanggal_dibuat:
            invoice.tanggal_dibuat = tanggal_dibuat
            invoice.save()

        # Create vendor trackers
        vendor_names = request.POST.getlist('vendor_names')
        for name in vendor_names:
            if name.strip():
                VendorTracker.objects.create(
                    invoice=invoice,
                    nama_vendor=name.strip(),
                )

        return redirect('admin_invoice', nomor_invoice=invoice.nomor_invoice)

    # GET — show form
    packages = Package.objects.all()
    clients = Client.objects.all()
    settings = BusinessSettings.get_solo()
    context = {
        'packages': packages,
        'clients': clients,
        'settings': settings,
    }
    return render(request, 'create_invoice.html', context)


def edit_info_view(request):
    """View untuk mengatur default bisnis dan CRUD Paket."""
    settings = BusinessSettings.get_solo()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. Update Business Settings
        if action == 'update_settings':
            settings.nama_bisnis = request.POST.get('nama_bisnis', settings.nama_bisnis)
            settings.email_bisnis = request.POST.get('email_bisnis', settings.email_bisnis)
            settings.lokasi = request.POST.get('lokasi', settings.lokasi)
            settings.nama_bank = request.POST.get('nama_bank', settings.nama_bank)
            settings.nomor_rekening = request.POST.get('nomor_rekening', settings.nomor_rekening)
            settings.atas_nama_rekening = request.POST.get('atas_nama_rekening', settings.atas_nama_rekening)
            settings.nomor_wa_konfirmasi = request.POST.get('nomor_wa_konfirmasi', settings.nomor_wa_konfirmasi)
            settings.save()
            # redirect untuk avoid form resubmission
            return redirect('edit_info')
            
        # 2. Add Package
        elif action == 'add_package':
            nama = request.POST.get('nama_paket', '')
            deskripsi = request.POST.get('deskripsi', '')
            harga = request.POST.get('harga_paket', 0)
            if nama:
                Package.objects.create(
                    nama_paket=nama,
                    deskripsi=deskripsi,
                    harga_paket=harga,
                )
            return redirect('edit_info')
            
        # 3. Edit Package
        elif action == 'edit_package':
            pkg_id = request.POST.get('package_id')
            if pkg_id:
                pkg = get_object_or_404(Package, id=pkg_id)
                pkg.nama_paket = request.POST.get('nama_paket', pkg.nama_paket)
                pkg.deskripsi = request.POST.get('deskripsi', pkg.deskripsi)
                pkg.harga_paket = request.POST.get('harga_paket', pkg.harga_paket)
                pkg.save()
            return redirect('edit_info')
            
        # 4. Delete Package
        elif action == 'delete_package':
            pkg_id = request.POST.get('package_id')
            if pkg_id:
                Package.objects.filter(id=pkg_id).delete()
            return redirect('edit_info')
            
    packages = Package.objects.all()
    context = {
        'settings': settings,
        'packages': packages,
    }
    return render(request, 'edit_info.html', context)
