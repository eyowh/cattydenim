from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Produk, Pesanan, ItemPesanan
import qrcode
from io import BytesIO
from django.core.files import File
import uuid

def get_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
    for produk_id, item in cart.items():
        produk = get_object_or_404(Produk, id=int(produk_id))
        subtotal = produk.get_harga_setelah_diskon() * item['jumlah']
        total += subtotal
        cart_items.append({
            'produk': produk,
            'jumlah': item['jumlah'],
            'subtotal': subtotal
        })
    
    return cart_items, total

def home(request):
    produk_list = Produk.objects.all().order_by('-created_at')
    best_sellers = Produk.objects.filter(is_best_seller=True)
    
    # Pagination
    paginator = Paginator(produk_list, 12)
    page_number = request.GET.get('page')
    produk = paginator.get_page(page_number)
    
    cart_items, cart_total = get_cart(request)
    cart_count = sum(item['jumlah'] for item in cart_items)
    
    context = {
        'produk': produk,
        'best_sellers': best_sellers,
        'cart_count': cart_count,
    }
    return render(request, 'home.html', context)

def detail_produk(request, id):
    produk = get_object_or_404(Produk, id=id)
    related_products = Produk.objects.filter(kategori=produk.kategori).exclude(id=id)[:4]
    
    cart_items, cart_total = get_cart(request)
    cart_count = sum(item['jumlah'] for item in cart_items)
    
    # Count total images for slider
    total_images = 0
    if produk.gambar:
        total_images += 1
    if produk.gambar2:
        total_images += 1
    if produk.gambar3:
        total_images += 1
    if produk.gambar4:
        total_images += 1
    
    context = {
        'produk': produk,
        'related_products': related_products,
        'cart_count': cart_count,
        'total_images': total_images,
    }
    return render(request, 'detail.html', context)

def add_to_cart(request, produk_id):
    if request.method == 'POST':
        produk = get_object_or_404(Produk, id=produk_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if produk.stok < quantity:
            messages.error(request, f'Stok tidak mencukupi! Stok tersedia: {produk.stok}')
            return redirect('detail', id=produk_id)
        
        cart = request.session.get('cart', {})
        
        if str(produk_id) in cart:
            cart[str(produk_id)]['jumlah'] += quantity
        else:
            cart[str(produk_id)] = {'jumlah': quantity}
        
        request.session['cart'] = cart
        messages.success(request, f'{produk.nama} berhasil ditambahkan ke keranjang!')
        
        return JsonResponse({
            'success': True,
            'message': f'{produk.nama} berhasil ditambahkan ke keranjang!',
            'cart_count': sum(item['jumlah'] for item in cart.values())
        })
    
    return redirect('detail', id=produk_id)

def cart(request):
    cart_items, total = get_cart(request)
    cart_count = sum(item['jumlah'] for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    }
    return render(request, 'cart.html', context)

def update_cart(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        action = request.POST.get('action')
        produk_id = request.POST.get('produk_id')
        
        if produk_id in cart:
            if action == 'increase':
                produk = get_object_or_404(Produk, id=int(produk_id))
                if produk.stok > cart[produk_id]['jumlah']:
                    cart[produk_id]['jumlah'] += 1
                else:
                    return JsonResponse({'success': False, 'message': 'Stok tidak mencukupi!'})
            elif action == 'decrease':
                if cart[produk_id]['jumlah'] > 1:
                    cart[produk_id]['jumlah'] -= 1
                else:
                    del cart[produk_id]
            elif action == 'remove':
                del cart[produk_id]
        
        request.session['cart'] = cart
        
        # Recalculate cart
        cart_items, total = get_cart(request)
        cart_count = sum(item['jumlah'] for item in cart_items)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'cart_count': cart_count,
            'cart_items': len(cart_items)
        })
    
    return JsonResponse({'success': False})

def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        
        if str(item_id) in cart:
            del cart[str(item_id)]
            request.session['cart'] = cart
            messages.success(request, 'Item berhasil dihapus dari keranjang!')
        
        return redirect('cart')
    
    return redirect('cart')

def checkout(request):
    cart_items, total = get_cart(request)
    
    if not cart_items:
        messages.warning(request, 'Keranjang belanja Anda kosong!')
        return redirect('cart')
    
    cart_count = sum(item['jumlah'] for item in cart_items)
    
    if request.method == 'POST':
        # Create order
        pesanan = Pesanan.objects.create(
            nama_pembeli=request.POST.get('nama_pembeli'),
            alamat=request.POST.get('alamat'),
            no_telepon=request.POST.get('no_telepon'),
            total_harga=total,
        )
        
        # Create order items
        for item in cart_items:
            ItemPesanan.objects.create(
                pesanan=pesanan,
                produk=item['produk'],
                jumlah=item['jumlah'],
                harga_satuan=item['produk'].get_harga_setelah_diskon()
            )
            
            # Update stock
            produk = item['produk']
            produk.stok -= item['jumlah']
            produk.save()
        
        # Generate QR Code
        qr_data = f"DENIM-{pesanan.id_pesanan}-{pesanan.total_harga}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        pesanan.qr_code.save(f'qr_{pesanan.id_pesanan}.png', File(qr_buffer))
        
        # Clear cart
        request.session['cart'] = {}
        
        messages.success(request, 'Pesanan berhasil dibuat!')
        return redirect('pembayaran', order_id=pesanan.id_pesanan)
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    }
    return render(request, 'checkout.html', context)

def process_checkout(request):
    # This function can handle AJAX checkout if needed
    return JsonResponse({'success': True})

def pembayaran(request, order_id):
    pesanan = get_object_or_404(Pesanan, id_pesanan=order_id)
    
    cart_items, cart_total = get_cart(request)
    cart_count = sum(item['jumlah'] for item in cart_items)
    
    context = {
        'pesanan': pesanan,
        'cart_count': cart_count,
    }
    return render(request, 'pembayaran.html', context)

def konfirmasi_pembayaran(request, order_id):
    pesanan = get_object_or_404(Pesanan, id_pesanan=order_id)
    
    if request.method == 'POST':
        if 'bukti_bayar' in request.FILES:
            pesanan.bukti_bayar = request.FILES['bukti_bayar']
            pesanan.status = 'dibayar'
            pesanan.save()
            messages.success(request, 'Bukti pembayaran berhasil diunggah!')
        else:
            messages.error(request, 'Silakan upload bukti pembayaran!')
        
        return redirect('pembayaran', order_id=order_id)
    
    return redirect('pembayaran', order_id=order_id)

def search_produk(request):
    query = request.GET.get('q', '')
    produk_list = Produk.objects.filter(
        Q(nama__icontains=query) | 
        Q(deskripsi__icontains=query)
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(produk_list, 12)
    page_number = request.GET.get('page')
    produk = paginator.get_page(page_number)
    
    cart_items, cart_total = get_cart(request)
    cart_count = sum(item['jumlah'] for item in cart_items)
    
    context = {
        'produk': produk,
        'query': query,
        'cart_count': cart_count,
    }
    return render(request, 'search.html', context)

def filter_kategori(request, kategori):
    produk_list = Produk.objects.filter(kategori=kategori).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(produk_list, 12)
    page_number = request.GET.get('page')
    produk = paginator.get_page(page_number)
    
    cart_items, cart_total = get_cart(request)
    cart_count = sum(item['jumlah'] for item in cart_items)
    
    context = {
        'produk': produk,
        'kategori': kategori,
        'cart_count': cart_count,
    }
    return render(request, 'kategori.html', context)