import uuid
from django.db import models
from django.utils import timezone


class Client(models.Model):
    """Model untuk menyimpan data klien wedding."""
    customer_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Customer ID',
    )
    nama_lengkap = models.CharField(max_length=200, verbose_name='Nama Lengkap')
    nomor_wa = models.CharField(max_length=20, verbose_name='Nomor WhatsApp')
    email = models.EmailField(blank=True, verbose_name='Email')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.customer_id:
            # Auto-generate unique customer_id format: #C-XXXX
            last = Client.objects.order_by('-id').first()
            next_num = (last.id + 1) if last else 1
            self.customer_id = f'#C-{next_num:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nama_lengkap} ({self.customer_id})'


class Package(models.Model):
    """Model untuk paket wedding yang ditawarkan."""
    nama_paket = models.CharField(max_length=200, verbose_name='Nama Paket')
    deskripsi = models.TextField(blank=True, verbose_name='Deskripsi')
    harga_paket = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='Harga Paket (Rp)',
    )

    class Meta:
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'
        ordering = ['harga_paket']

    def __str__(self):
        return f'{self.nama_paket} - Rp {self.harga_paket:,.0f}'


class InvoiceSequence(models.Model):
    """Model untuk melacak urutan nomor invoice terakhir per tahun agar nomor tidak duplikat saat ada invoice dihapus."""
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Invoice Sequence'

class Invoice(models.Model):
    """Model invoice untuk tagihan klien."""

    STATUS_CHOICES = [
        ('menunggu', 'Menunggu Pembayaran'),
        ('dp', 'DP Terbayar'),
        ('proses', 'Proses'),
        ('lunas', 'Lunas'),
        ('overdue', 'Overdue'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='Client',
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='Package',
    )
    nomor_invoice = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='Nomor Invoice',
    )
    tanggal_dibuat = models.DateField(
        default=timezone.now,
        verbose_name='Tanggal Dibuat',
    )
    total_tagihan = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='Total Tagihan (Rp)',
    )
    nominal_terbayar = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name='Nominal Terbayar (Rp)',
    )
    request_client = models.TextField(
        blank=True,
        null=True,
        verbose_name='Request Client',
    )
    sisa_tagihan = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        editable=False,
        verbose_name='Sisa Tagihan (Rp)',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='menunggu',
        verbose_name='Status',
    )
    bank_name = models.CharField(max_length=100, blank=True, verbose_name='Nama Bank')
    bank_account = models.CharField(max_length=50, blank=True, verbose_name='Nomor Rekening')
    bank_account_name = models.CharField(max_length=100, blank=True, verbose_name='Atas Nama Rekening')
    wa_number = models.CharField(max_length=20, blank=True, verbose_name='Nomor WhatsApp Konfirmasi')

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-tanggal_dibuat']

    def save(self, *args, **kwargs):
        # Auto-generate nomor_invoice format: INV-YYYY-XXXX
        if not self.nomor_invoice:
            year = timezone.now().year
            from django.db import transaction
            with transaction.atomic():
                seq, created = InvoiceSequence.objects.select_for_update().get_or_create(year=year)
                if created:
                    # Jika sequence baru dibuat, cari invoice terakhir di tahun ini sebagai baseline awal
                    last = Invoice.objects.filter(
                        nomor_invoice__startswith=f'INV-{year}'
                    ).order_by('-nomor_invoice').first()
                    if last:
                        try:
                            seq.last_number = int(last.nomor_invoice.split('-')[-1])
                        except ValueError:
                            seq.last_number = 0
                
                seq.last_number += 1
                seq.save()
                self.nomor_invoice = f'INV-{year}-{seq.last_number:04d}'

        # Auto-calculate sisa_tagihan
        self.sisa_tagihan = self.total_tagihan - self.nominal_terbayar
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nomor_invoice} - {self.client.nama_lengkap}'


class VendorTracker(models.Model):
    """Model untuk tracking progress vendor."""

    STATUS_CHOICES = [
        ('menunggu', 'Menunggu'),
        ('proses', 'Proses'),
        ('selesai', 'Selesai'),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='vendors',
        verbose_name='Invoice',
    )
    nama_vendor = models.CharField(
        max_length=200,
        verbose_name='Nama Vendor',
        help_text='Contoh: Venue, Katering, MUA',
    )
    progress_persen = models.IntegerField(
        default=0,
        verbose_name='Progress (%)',
        help_text='Persentase progress vendor (0-100)',
    )
    status_pembayaran = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='menunggu',
        verbose_name='Status',
    )

    class Meta:
        verbose_name = 'Vendor Tracker'
        verbose_name_plural = 'Vendor Trackers'
        ordering = ['nama_vendor']

    def __str__(self):
        return f'{self.nama_vendor} ({self.invoice.nomor_invoice}) - {self.progress_persen}%'


class BusinessSettings(models.Model):
    """Model singleton untuk menyimpan pengaturan default bisnis."""
    nama_bisnis = models.CharField(max_length=200, default='Berkat Wedding Organizer')
    email_bisnis = models.EmailField(default='admin@berkatwo.com')
    lokasi = models.TextField(default='Elegansi Abadi untuk Hari Bahagia Anda.\nJl. Slamet Riyadi No. 450, Solo, Jawa Tengah.')
    terms_and_conditions = models.TextField(default='Booking tanpa DP = No Keep tanggal & vendor\nBooking min. DP 10% dari package yang diambil\nBiaya boleh dicicil tiap bulannya hingga pelunasan h-7\nPelunasan H-7 hari acara berlangsung\nBiaya diatas belum termasuk charge transportasi bila ada vendor yang dipilih client dari luar kota\nBiaya diatas untuk acara dalam 1 hari yang sama\nUpgrade MC Akad Rp. 300.000')
    nama_bank = models.CharField(max_length=100, default='Bank Central Asia (BCA)')
    nomor_rekening = models.CharField(max_length=50, default='1234567890')
    atas_nama_rekening = models.CharField(max_length=100, default='Berkat Wedding Organizer')
    nomor_wa_konfirmasi = models.CharField(max_length=20, default='62895337452311')

    class Meta:
        verbose_name = 'Business Settings'
        verbose_name_plural = 'Business Settings'

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Business Settings'
