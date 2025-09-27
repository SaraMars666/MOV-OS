from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Venta, VentaDetalle, AperturaCierreCaja
from products.models import Product
from decimal import Decimal
import json
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.db import models

def format_currency(value):
    try:
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except Exception:
        return value

def format_clp(value):
    """
    Convierte un valor (en centavos) a pesos chilenos dividiendo entre 100
    y formateándolo a dos decimales con signo de peso.
    """
    try:
        pesos_val = float(value) / 100.0
        # Puedes ajustar el formateo según convención; en este ejemplo usamos punto para miles y coma para decimales.
        return "{:,.2f}".format(pesos_val)
    except Exception:
        return value

@transaction.atomic
@login_required
def cashier_dashboard(request):
    """
    Muestra la interfaz del cajero y procesa las ventas.
    Si no hay caja abierta, redirige a 'abrir_caja'.
    """
    caja_abierta = AperturaCierreCaja.objects.filter(usuario=request.user, estado='abierta').first()
    if not caja_abierta:
        return redirect('abrir_caja')

    if request.method == 'GET':
        productos = Product.objects.all()
        return render(request, 'cashier/cashier.html', {
            'productos': productos,
            'caja_abierta': caja_abierta
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            carrito = data.get('carrito', [])
            tipo_venta = data.get('tipo_venta', 'boleta')
            forma_pago = data.get('forma_pago', 'efectivo')
            cliente_paga = Decimal(str(data.get('cliente_paga', '0')))
            numero_transaccion = data.get('numero_transaccion', '').strip()
            banco = data.get('banco', '').strip() if forma_pago == "transferencia" else ""
            
            if forma_pago in ["debito", "credito", "transferencia"] and not numero_transaccion:
                return JsonResponse({
                    "error": "El número de transacción es obligatorio para pagos con tarjeta y transferencia."
                }, status=400)
            if forma_pago == "transferencia" and not banco:
                return JsonResponse({
                    "error": "Debe ingresar el nombre del banco para pagos por transferencia."
                }, status=400)
            if not carrito:
                return JsonResponse({"error": "El carrito está vacío."}, status=400)
        
            total = Decimal('0.00')
            for item in carrito:
                producto = get_object_or_404(Product, id=item.get('producto_id'))
                cantidad = int(item.get('cantidad', 1))
                total += Decimal(str(cantidad)) * producto.precio_venta
        
            if forma_pago == 'efectivo' and cliente_paga < total:
                return JsonResponse({
                    "error": f"Pago insuficiente. El total es ${format_currency(total)}, pero el cliente pagó ${format_currency(cliente_paga)}."
                }, status=400)
        
            with transaction.atomic():
                venta = Venta.objects.create(
                    empleado=request.user,
                    tipo_venta=tipo_venta,
                    forma_pago=forma_pago,
                    total=Decimal('0.00'),
                    cliente_paga=cliente_paga if forma_pago == "efectivo" else Decimal('0.00'),
                    vuelto_entregado=Decimal('0.00'),
                    numero_transaccion=numero_transaccion if forma_pago in ["debito", "credito", "transferencia"] else "",
                    banco=banco
                )
            
                for item in carrito:
                    producto = get_object_or_404(Product, id=item.get('producto_id'))
                    cantidad = int(item.get('cantidad', 1))
                
                    if not producto.permitir_venta_sin_stock and producto.stock < cantidad:
                        return JsonResponse({"error": f"El producto '{producto.nombre}' no tiene suficiente stock."}, status=400)
                
                for item in carrito:
                    producto = get_object_or_404(Product, id=item.get('producto_id'))
                    cantidad = int(item.get('cantidad', 1))
                    producto.stock = max(0, producto.stock - cantidad)
                    producto.save()
                    
                    VentaDetalle.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio_venta
                    )
            
                venta.total = total
                if forma_pago == "efectivo":
                    venta.vuelto_entregado = max(Decimal('0.00'), cliente_paga - total)
                venta.save()
        
            reporte_url = reverse('reporte_venta', args=[venta.id])
            return JsonResponse({
                "success": True,
                "mensaje": "Compra confirmada con éxito.",
                "reporte_url": reporte_url
            })
    
        except (json.JSONDecodeError, KeyError, ValueError, Product.DoesNotExist) as e:
            return JsonResponse({"error": f"Error en los datos enviados o producto no encontrado: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Ocurrió un error inesperado: {str(e)}"}, status=500)

    return JsonResponse({"error": "Método no permitido."}, status=405)

# 📌 CERRAR CAJA
@login_required
def cerrar_caja(request):
    caja_abierta = AperturaCierreCaja.objects.filter(usuario=request.user, estado='abierta').first()
    if not caja_abierta:
        return JsonResponse({"error": "No tienes una caja abierta para cerrar."}, status=403)

    # 📊 Obtener ventas del día
    ventas_del_dia = Venta.objects.filter(empleado=request.user, fecha__gte=caja_abierta.fecha_apertura)

    # 📊 Calcular totales
    total_ventas = ventas_del_dia.aggregate(total=models.Sum('total'))['total'] or Decimal('0.00')
    total_efectivo = ventas_del_dia.filter(forma_pago='efectivo').aggregate(total=models.Sum('total'))['total'] or Decimal('0.00')
    total_credito = ventas_del_dia.filter(forma_pago='credito').aggregate(total=models.Sum('total'))['total'] or Decimal('0.00')
    total_debito = ventas_del_dia.filter(forma_pago='debito').aggregate(total=models.Sum('total'))['total'] or Decimal('0.00')
    vuelto_entregado = ventas_del_dia.filter(forma_pago='efectivo').aggregate(total=models.Sum('vuelto_entregado'))['total'] or Decimal('0.00')

    # 📌 Calcular efectivo final (NO incluir pagos con tarjeta)
    efectivo_final = caja_abierta.efectivo_inicial + total_efectivo - vuelto_entregado

    if request.method == 'POST':
        caja_abierta.ventas_totales = total_ventas
        caja_abierta.total_ventas_efectivo = total_efectivo 
        caja_abierta.total_ventas_credito = total_credito 
        caja_abierta.total_ventas_debito = total_debito 
        caja_abierta.vuelto_entregado = vuelto_entregado
        caja_abierta.efectivo_final = efectivo_final 
        caja_abierta.estado = 'cerrada'
        caja_abierta.fecha_cierre = timezone.now()
        caja_abierta.save()

        return JsonResponse({
            "success": True,
            "mensaje": "Caja cerrada correctamente.",
            "caja_id": caja_abierta.id
        })

    return JsonResponse({"error": "Método no permitido."}, status=405)

# 📌 DETALLE DE CIERRE DE CAJA
@login_required
def detalle_caja(request, caja_id):
    """Muestra el resumen de la caja cerrada con los valores formateados en pesos chilenos."""
    caja = get_object_or_404(AperturaCierreCaja, id=caja_id)
    contexto = {
        'caja': caja,
        'formatted_efectivo_inicial': "$" + format_clp(caja.efectivo_inicial or Decimal('0.00')),
        'formatted_total_debito': "$" + format_clp(caja.total_ventas_debito or Decimal('0.00')),
        'formatted_total_credito': "$" + format_clp(caja.total_ventas_credito or Decimal('0.00')),
        'formatted_total_efectivo': "$" + format_clp(caja.total_ventas_efectivo or Decimal('0.00')),
        'formatted_vuelto_entregado': "$" + format_clp(caja.vuelto_entregado or Decimal('0.00')),
        'formatted_efectivo_final': "$" + format_clp(caja.efectivo_final or caja.efectivo_inicial or Decimal('0.00')),
        'formatted_total_ventas': "$" + format_clp(caja.ventas_totales or Decimal('0.00'))
    }
    return render(request, 'cashier/detalle_caja.html', contexto)

# 📌 HISTORIAL DE CAJAS
@login_required
def historial_caja(request):
    """Lista todas las cajas abiertas/cerradas."""
    historial_cajas = AperturaCierreCaja.objects.all().order_by('-fecha_apertura')
    return render(request, 'cashier/historial_caja.html', {'historial_cajas': historial_cajas})

# 📌 BUSCAR PRODUCTO
@login_required
def buscar_producto(request):
    """
    Busca productos por nombre o código de barras.
    Devuelve un JSON con la lista de productos encontrados.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'productos': []})
    productos = Product.objects.filter(
        Q(nombre__icontains=query) |
        Q(producto_id__icontains=query) |
        Q(codigo_alternativo__icontains=query) | 
        Q(codigo_barras__icontains=query)
    )
    resultados = [{
        'id': p.id,
        'nombre': p.nombre,
        'precio_venta': str(p.precio_venta)
    } for p in productos]
    return JsonResponse({'productos': resultados})

# 📌 REPORTE DE VENTA
@login_required
def reporte_venta(request, venta_id):
    """
    Reporte detallado de una venta.
    Se calculan en la vista los valores formateados y se pasan al template mediante el contexto.
    """
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = venta.detalles.all()
    
    total_formatted = "$" + format_currency(getattr(venta, 'total', 0))
    cliente_paga_formatted = "$" + format_currency(getattr(venta, 'cliente_paga', 0))
    vuelto_formatted = "$" + format_currency(getattr(venta, 'vuelto_entregado', 0))
    
    # Construir una lista de diccionarios en lugar de modificar la instancia
    detalles_data = []
    for detalle in detalles:
        subtotal = detalle.cantidad * detalle.precio_unitario
        detalles_data.append({
            'producto': detalle.producto,
            'cantidad': detalle.cantidad,
            'precio_unitario': detalle.precio_unitario,
            'formatted_subtotal': "$" + format_currency(subtotal)
        })
    
    context = {
         'venta': venta,
         'detalles': detalles_data,
         'formatted_total': total_formatted,
         'formatted_cliente_paga': cliente_paga_formatted,
         'formatted_vuelto_entregado': vuelto_formatted,
    }
    return render(request, 'cashier/reporte_venta.html', context)

# 📌 AJUSTAR CANTIDAD EN EL CARRITO
@login_required
def ajustar_cantidad(request):
    """Ajusta la cantidad de un producto en el carrito de compras."""
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido."}, status=405)

    try:
        data = json.loads(request.body)
        producto_id = int(data.get('producto_id'))
        cambio_cantidad = int(data.get('cantidad'))
        
        producto = get_object_or_404(Product, id=producto_id)
        
        carrito = request.session.get('carrito', [])
        
        found = False
        for item in carrito:
            if item['producto_id'] == producto_id:
                found = True
                nueva_cantidad = item['cantidad'] + cambio_cantidad
                
                if nueva_cantidad <= 0:
                    carrito.remove(item)
                else:
                    item['cantidad'] = nueva_cantidad
                break
        
        if not found:
            return JsonResponse({"error": "Producto no encontrado en el carrito."}, status=404)

        request.session['carrito'] = carrito
        request.session.modified = True

        return JsonResponse({"mensaje": "Cantidad ajustada correctamente.", "carrito": carrito})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# 📌 AGREGAR PRODUCTO AL CARRITO
@login_required
def agregar_al_carrito(request):
    """Añade un producto al carrito, fijando la cantidad en 1 siempre."""
    caja_abierta = AperturaCierreCaja.objects.filter(usuario=request.user, estado='abierta').first()
    if not caja_abierta:
        return JsonResponse({'error': 'No tienes una caja abierta.'}, status=403)

    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        producto_id = data.get("producto_id")
        # Se fija la cantidad a 1 siempre
        cantidad = 1

        producto = get_object_or_404(Product, id=producto_id)
        
        if not producto.permitir_venta_sin_stock and producto.stock < cantidad:
            return JsonResponse({"error": "Stock insuficiente para este producto."}, status=400)

        carrito = request.session.get('carrito', [])

        # Si el producto ya existe en el carrito, se resetea su cantidad a 1.
        found = False
        for item in carrito:
            if item['producto_id'] == producto.id:
                item['cantidad'] = cantidad
                found = True
                break

        if not found:
            carrito.append({
                'producto_id': producto.id,
                'nombre': producto.nombre,
                'precio': str(producto.precio_venta),
                'cantidad': cantidad,
            })

        request.session['carrito'] = carrito
        request.session.modified = True

        return JsonResponse({'mensaje': 'Producto agregado al carrito', 'carrito': carrito})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# 📌 LISTAR PRODUCTOS DEL CARRITO
@login_required
def listar_carrito(request):
    """Devuelve el contenido del carrito actual."""
    carrito = request.session.get('carrito', [])
    return JsonResponse({'carrito': carrito})

# 📌 LIMPIAR EL CARRITO
@login_required
def limpiar_carrito(request):
    """Elimina todos los productos del carrito."""
    request.session['carrito'] = []
    request.session.modified = True
    return JsonResponse({'mensaje': 'Carrito limpio con éxito'})

def delete_all_sales_and_cash_history(request):
    """
    Elimina todo el historial de ventas y registros de caja.
    Esta vista debe ser usada solo una vez antes del despliegue final
    y luego eliminada del código.
    """
    if request.method == 'POST':
        try:
            Venta.objects.all().delete()
            AperturaCierreCaja.objects.all().delete()
            messages.success(request, '¡Éxito! Todo el historial de ventas y caja ha sido eliminado.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al eliminar los datos: {e}')
    return redirect('products_management')

# 📌 ABRIR CAJA
@login_required
def abrir_caja(request):
    """
    Vista para abrir una caja. Si el método es GET, muestra el formulario para abrir caja;
    si es POST, procesa la apertura.
    """
    if request.method == "POST":
        # Aquí debería ir la lógica para abrir la caja.
        # Por ejemplo, se pueden leer datos del POST y crear un objeto AperturaCierreCaja.
        # Suponiendo que la apertura requiere al menos un monto inicial:
        monto_inicial = Decimal(request.POST.get('efectivo_inicial', '0'))
        # Crear la caja abierta:
        caja = AperturaCierreCaja.objects.create(
            usuario=request.user,
            efectivo_inicial=monto_inicial,
            estado='abierta'
        )
        # Redirige al dashboard del cajero una vez que se abre la caja.
        return redirect('cashier_dashboard')
    # Si es GET, muestra el formulario para abrir caja.
    return render(request, 'cashier/abrir_caja.html')
