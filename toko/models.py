from django.db import models

class Produk(models.Model):
    KATEGORI_CHOICES = [
        ('celana', 'Celana Jeans'),
        ('jaket', 'Jaket Denim'),
        ('kaos', 'Kaos Denim'),
        ('aksesoris', 'Aksesoris Denim'),
    ]
    
    nama = models.CharField(max_length=200)
    harga = models.IntegerField()
    deskripsi = models.TextField()
    gambar = models.ImageField(upload_to='produk/')
    gambar2 = models.ImageField(upload_to='produk/', null=True, blank=True)
    gambar3 = models.ImageField(upload_to='produk/', null=True, blank=True)
    gambar4 = models.ImageField(upload_to='produk/', null=True, blank=True)
    stok = models.IntegerField()
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES, default='celana')
    is_best_seller = models.BooleanField(default=False)
    diskon = models.IntegerField(default=0)  # persentase diskon
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.nama} ({self.get_kategori_display()})"

    def get_kategori_display(self):
        for kategori, display in self.KATEGORI_CHOICES:
            if kategori == self.kategori:
                return display
        return self.kategori
    
    def get_harga_setelah_diskon(self):
        if self.diskon > 0:
            return int(self.harga * (1 - self.diskon / 100))
        return self.harga


class Pesanan(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('dibayar', 'Dibayar'),
        ('diproses', 'Diproses'),
        ('dikirim', 'Dikirim'),
        ('selesai', 'Selesai'),
    )
    
    id_pesanan = models.CharField(max_length=20, unique=True, null=True, blank=True)  # untuk QR code
    nama_pembeli = models.CharField(max_length=100)
    alamat = models.TextField()
    no_telepon = models.CharField(max_length=15, blank=True)
    total_harga = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    bukti_bayar = models.ImageField(upload_to='bukti/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='qrcode/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Pesanan {self.id_pesanan} - {self.nama_pembeli}"
    
    def save(self, *args, **kwargs):
        if not self.id_pesanan:
            import uuid
            self.id_pesanan = f"DENIM-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class ItemPesanan(models.Model):
    pesanan = models.ForeignKey(Pesanan, on_delete=models.CASCADE, related_name='items')
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    jumlah = models.IntegerField()
    harga_satuan = models.IntegerField(default=0)  # harga saat pembelian
    
    def __str__(self):
        return f"{self.jumlah}x {self.produk.nama}"
    
    def get_total_harga(self):
        return self.jumlah * self.harga_satuan