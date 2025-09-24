from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction, models
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
import json
from decimal import Decimal

from .models import Venta, VentaDetalle, AperturaCierreCaja
from products.models import Product
from .forms import AperturaCajaForm

# 📌 ABRIR CAJA
@login_required
def abrir_caja(request):
    """Verifica si ya hay una caja abierta. Si no, abre una nueva con el monto inicial."""
    caja_abierta = AperturaCierreCaja.objects.filter(usuario=request.user, estado='abierta').first()
    
    if caja_abierta:
        messages.info(request, "Ya tienes una caja abierta.")
        return redirect('cashier_dashboard')

    if request.method == 'POST':
        try:
            # Usar Decimal para el manejo de dinero
            efectivo_inicial = Decimal(request.POST.get('efectivo_inicial', '0.00'))
            AperturaCierreCaja.objects.create(
                usuario=request.user,
                efectivo_inicial=efectivo_inicial,
                estado='abierta'
            )
            messages.success(request, f"Caja abierta con éxito. Monto inicial: ${efectivo_inicial:,.2f}")
            return redirect('cashier_dashboard')
        except (ValueError, TypeError):
            messages.error(request, "El monto inicial debe ser un número válido.")
            return redirect('abrir_caja')

    return render(request, 'cashier/abrir_caja.html')

# 📌 DASHBOARD DEL CAJERO Y PROCESAMIENTO DE VENTA
@transaction.atomic
@login_required
def cashier_dashboard(request):
    """
    Maneja la vista del cajero y el procesamiento de ventas.
    GET: Muestra la interfaz del cajero.
    POST: Procesa la venta y actualiza el stock.
    """
    caja_abierta = AperturaCierreCaja.objects.filter(usuario=request.user, estado='abierta').first()

    if not caja_abierta:
        messages.warning(request, "No tienes una caja abierta. Debes abrir una caja para realizar ventas.")
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

            if not carrito:
                return JsonResponse({"error": "El carrito está vacío."}, status=400)

            total = Decimal('0.00')
            for item in carrito:
                producto = get_object_or_404(Product, id=item.get('producto_id'))
                cantidad = int(item.get('cantidad', 1))
                total += Decimal(str(cantidad)) * producto.precio_venta

            # Verificación de pago insuficiente solo para efectivo
            if forma_pago == 'efectivo' and cliente_paga < total:
                return JsonResponse({
                    "error": f"Pago insuficiente. El total es ${total:,.2f}, pero el cliente pagó ${cliente_paga:,.2f}."
                }, status=400)

            with transaction.atomic():
                venta = Venta.objects.create(
                    empleado=request.user,
                    tipo_venta=tipo_venta,
                    forma_pago=forma_pago,
                    total=Decimal('0.00'),
                    vuelto_entregado=Decimal('0.00')
                )

                for item in carrito:
                    producto = get_object_or_404(Product, id=item.get('producto_id'))
                    cantidad = int(item.get('cantidad', 1))

                    if not producto.permitir_venta_sin_stock and producto.stock < cantidad:
                        return JsonResponse({"error": f"El producto '{producto.nombre}' no tiene suficiente stock."}, status=400)

                    producto.stock -= cantidad
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
    """Muestra el resumen de la caja cerrada en el orden correcto."""
    caja = get_object_or_404(AperturaCierreCaja, id=caja_id)
    contexto = {
        'caja': caja,
        'efectivo_inicial': caja.efectivo_inicial or Decimal('0.00'),
        'total_debito': caja.total_ventas_debito or Decimal('0.00'),
        'total_credito': caja.total_ventas_credito or Decimal('0.00'),
        'vuelto_entregado': caja.vuelto_entregado or Decimal('0.00'),
        'efectivo_final': caja.efectivo_final or caja.efectivo_inicial, 
        'total_ventas': caja.ventas_totales or Decimal('0.00')
    }
    return render(request, 'cashier/cerrar_caja.html', contexto)

# 📌 HISTORIAL DE CAJAS
@login_required
def historial_caja(request):
    """Lista todas las cajas abiertas/cerradas."""
    historial_cajas = AperturaCierreCaja.objects.all().order_by('-fecha_apertura')
    return render(request, 'cashier/historial_caja.html', {'historial_cajas': historial_cajas})

# 📌 BUSCAR PRODUCTO
@login_required
def buscar_producto(request):
    """Busca productos por nombre o código de barras."""
    query = request.GET.get('q', '').strip()
    productos = Product.objects.filter(
        Q(nombre__icontains=query) |
        Q(producto_id__icontains=query) |
        Q(codigo_alternativo__icontains=query) | 
        Q(codigo_barras__icontains=query)
    ) if query else []
    
    resultados = [{'id': p.id, 'nombre': p.nombre, 'precio_venta': str(p.precio_venta)} for p in productos]
    return JsonResponse({'productos': resultados})

# 📌 REPORTE DE VENTA
@login_required
def reporte_venta(request, venta_id):
    """Muestra el detalle de una venta específica."""
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = venta.detalles.all()
    return render(request, 'cashier/reporte_venta.html', {'venta': venta, 'detalles': detalles})

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
    """Añade un producto al carrito, verificando stock y caja abierta."""
    caja_abierta = AperturaCierreCaja.objects.filter(usuario=request.user, estado='abierta').first()
    if not caja_abierta:
        return JsonResponse({'error': 'No tienes una caja abierta.'}, status=403)

    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        producto_id = data.get("producto_id")
        cantidad = int(data.get("cantidad", 1))

        producto = get_object_or_404(Product, id=producto_id)
        
        if not producto.permitir_venta_sin_stock and producto.stock < cantidad:
            return JsonResponse({"error": "Stock insuficiente para este producto."}, status=400)

        carrito = request.session.get('carrito', [])

        for item in carrito:
            if item['producto_id'] == producto.id:
                item['cantidad'] += cantidad
                break
        else:
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
