from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Produk, Pesanan, ItemPesanan

@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = ('nama', 'kategori', 'harga', 'get_harga_setelah_diskon', 'stok', 'is_best_seller', 'diskon', 'gambar_preview')
    list_filter = ('kategori', 'is_best_seller', 'created_at')
    search_fields = ('nama', 'deskripsi')
    list_editable = ('harga', 'stok', 'is_best_seller', 'diskon')
    readonly_fields = ('created_at', 'get_harga_setelah_diskon', 'gambar_preview')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informasi Produk', {
            'fields': ('nama', 'kategori', 'deskripsi')
        }),
        ('Harga & Stok', {
            'fields': ('harga', 'diskon', 'get_harga_setelah_diskon', 'stok')
        }),
        ('Gambar', {
            'fields': ('gambar', 'gambar2', 'gambar3', 'gambar4', 'gambar_preview')
        }),
        ('Status', {
            'fields': ('is_best_seller',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def gambar_preview(self, obj):
        images = []
        if obj.gambar:
            images.append(obj.gambar.url)
        if obj.gambar2:
            images.append(obj.gambar2.url)
        if obj.gambar3:
            images.append(obj.gambar3.url)
        if obj.gambar4:
            images.append(obj.gambar4.url)
        
        if images:
            image_tags = []
            for img_url in images[:4]:  # Max 4 images
                image_tags.append(f'<img src="{img_url}" width="60" height="60" style="object-fit: cover; border-radius: 4px; margin: 2px;" />')
            return format_html(''.join(image_tags))
        return "Tidak ada gambar"
    gambar_preview.short_description = 'Preview Gambar'

@admin.register(Pesanan)
class PesananAdmin(admin.ModelAdmin):
    list_display = ('id_pesanan', 'nama_pembeli', 'no_telepon', 'total_harga', 'status', 'created_at', 'qr_code_preview')
    list_filter = ('status', 'created_at')
    search_fields = ('id_pesanan', 'nama_pembeli', 'alamat')
    readonly_fields = ('id_pesanan', 'total_harga', 'created_at', 'updated_at', 'qr_code_preview')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informasi Pesanan', {
            'fields': ('id_pesanan', 'nama_pembeli', 'no_telepon', 'alamat')
        }),
        ('Status & Pembayaran', {
            'fields': ('status', 'total_harga', 'bukti_bayar', 'qr_code', 'qr_code_preview')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="80" height="80" style="object-fit: contain;" />', obj.qr_code.url)
        return "Belum ada QR Code"
    qr_code_preview.short_description = 'QR Code'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('items')

@admin.register(ItemPesanan)
class ItemPesananAdmin(admin.ModelAdmin):
    list_display = ('pesanan', 'produk', 'jumlah', 'harga_satuan', 'get_total_harga')
    list_filter = ('pesanan__status', 'produk__kategori')
    search_fields = ('pesanan__id_pesanan', 'pesanan__nama_pembeli', 'produk__nama')
    readonly_fields = ('get_total_harga',)
    
    def get_total_harga(self, obj):
        return obj.get_total_harga()
    get_total_harga.short_description = 'Total Harga'

# Custom admin site configuration
admin.site.site_header = 'Catty Denim Admin'
admin.site.site_title = 'Catty Denim'
admin.site.index_title = 'Selamat datang di Dashboard Catty Denim'