import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.db.models import Q, Sum, F, Count
from django.db.models.functions import Cast
from django.utils import timezone
import datetime
from decimal import Decimal, ROUND_HALF_UP

from cashier.models import Venta, VentaDetalle, AperturaCierreCaja  
from auth_app.models import User

logger = logging.getLogger(__name__)

def format_clp(value):
    try:
        # No mostramos decimales y usamos punto como separador de miles
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except Exception:
        return value

@login_required
def report_dashboard(request):
    """Pantalla principal para la generación de reportes"""
    return render(request, 'reports/report_dashboard.html')

@login_required
def sales_dashboard(request):
    """Pantalla principal de Gestión de Ventas con opciones"""
    return render(request, 'reports/sales_dashboard.html')

@login_required
def sales_history(request):
    """Historial de Ventas"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    empleado_id = request.GET.get('empleado')
    page = request.GET.get('page', 1)

    ventas = Venta.objects.all().order_by('-fecha')

    if fecha_inicio:
        try:
            fecha_inicio_obj = timezone.make_aware(datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d'))
            ventas = ventas.filter(fecha__gte=fecha_inicio_obj)
        except ValueError:
            ventas = Venta.objects.none()
    if fecha_fin:
        try:
            fecha_fin_obj = timezone.make_aware(datetime.datetime.strptime(fecha_fin, '%Y-%m-%d'))
            fecha_fin_obj += datetime.timedelta(days=1, seconds=-1)
            ventas = ventas.filter(fecha__lte=fecha_fin_obj)
        except ValueError:
            ventas = Venta.objects.none()
    if empleado_id:
        try:
            empleado_id = int(empleado_id)
            ventas = ventas.filter(empleado_id=empleado_id)
        except ValueError:
            ventas = Venta.objects.none()

    paginator = Paginator(ventas, 8)
    sales_page = paginator.get_page(page)
    for sale in sales_page:
        sale.display_total = "$" + format_clp(sale.total)
    empleados = User.objects.all()

    return render(request, 'reports/sales_history.html', {
        'sales': sales_page,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'empleado_id': empleado_id if empleado_id else None,
        'empleados': empleados,
    })

@login_required
def cash_history(request):
    """Historial de Caja con filtros por ID, cajero y rango de fechas."""
    id_caja_filtro = request.GET.get('id_caja')
    cajero_filtro = request.GET.get('cajero')
    fecha_inicio_filtro = request.GET.get('fecha_inicio')
    fecha_fin_filtro = request.GET.get('fecha_fin')
    page = request.GET.get('page', 1)
    per_page_options = [5, 10, 15, 20]
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    if per_page not in per_page_options:
        per_page = 10

    cajas = AperturaCierreCaja.objects.all().order_by('-fecha_apertura')
    if id_caja_filtro:
        try:
            cajas = cajas.filter(id=int(id_caja_filtro))
        except ValueError:
            cajas = AperturaCierreCaja.objects.none()
    if cajero_filtro:
        cajas = cajas.filter(usuario__username__icontains=cajero_filtro)
    if fecha_inicio_filtro:
        try:
            fecha_inicio_obj = parse_date(fecha_inicio_filtro)
            if fecha_inicio_obj:
                cajas = cajas.filter(fecha_apertura__gte=fecha_inicio_obj)
        except ValueError:
            cajas = AperturaCierreCaja.objects.none()
    if fecha_fin_filtro:
        try:
            fecha_fin_obj = parse_date(fecha_fin_filtro)
            if fecha_fin_obj:
                cajas = cajas.filter(fecha_apertura__lte=fecha_fin_obj)
        except ValueError:
            cajas = AperturaCierreCaja.objects.none()

    paginator = Paginator(cajas, per_page)
    cash_page = paginator.get_page(page)
    for caja in cash_page:
        if caja.estado == 'cerrada':
            caja.vuelto_entregado = caja.vuelto_entregado or 0
            caja.efectivo_final = caja.efectivo_final or (caja.efectivo_inicial + caja.total_ventas_efectivo - caja.vuelto_entregado)
        caja.formatted_ventas_totales = "$" + format_clp(getattr(caja, "total_ventas_efectivo", 0))

    return render(request, 'reports/cash_history.html', {
        'cajas': cash_page,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'id_caja_filtro': id_caja_filtro,
        'cajero_filtro': cajero_filtro,
        'fecha_inicio_filtro': fecha_inicio_filtro,
        'fecha_fin_filtro': fecha_fin_filtro,
    })

@login_required
def sales_report(request, sale_id):
    """
    Reporte detallado de una venta. Verifica que la venta exista y que tenga detalles.
    Se usan propiedades para inyectar valores formateados.
    """
    try:
        venta = get_object_or_404(Venta, id=sale_id)
        # Obtiene los detalles usando el related_name definido en el modelo
        detalles = venta.detalles.all()
        logger.info("Venta %s encontrada con %d detalle(s).", sale_id, detalles.count())

        # Se formatean los campos de la venta
        venta.formatted_total = "$" + format_clp(venta.total or 0)
        venta.formatted_cliente_paga = "$" + format_clp(venta.cliente_paga or 0)
        venta.formatted_vuelto_entregado = "$" + format_clp(venta.vuelto_entregado or 0)

        # Se calcula y asigna el subtotal formateado para cada detalle
        for detalle in detalles:
            subtotal = detalle.cantidad * detalle.precio_unitario
            detalle.formatted_subtotal = "$" + format_clp(subtotal)

        return render(request, 'reports/sales_report.html', {'venta': venta, 'detalles': detalles})
    except Exception as e:
        logger.error("Error en sales_report (ID:%s): %s", sale_id, str(e))
        return render(request, 'reports/sales_report.html', {
            'error': str(e),
            'venta': None,
            'detalles': None
        })

@login_required
def advanced_reports(request):
    """
    Reporte Avanzado que muestra los KPIs y gráficos.
    """
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    try:
        if fecha_inicio_str:
            fecha_inicio = datetime.datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            fecha_inicio = timezone.make_aware(fecha_inicio)
        else:
            fecha_inicio = timezone.now() - datetime.timedelta(days=30)
    except ValueError:
        fecha_inicio = timezone.now() - datetime.timedelta(days=30)
    try:
        if fecha_fin_str:
            fecha_fin = datetime.datetime.strptime(fecha_fin_str, '%Y-%m-%d')
            fecha_fin = timezone.make_aware(fecha_fin) + datetime.timedelta(days=1, seconds=-1)
        else:
            fecha_fin = timezone.now()
    except ValueError:
        fecha_fin = timezone.now()
    
    ventas_qs = Venta.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
    
    agg_ventas = ventas_qs.aggregate(
        ingreso_total=Sum('total'),
        num_transacciones=Count('id')
    )
    ingreso_total = agg_ventas.get('ingreso_total') or Decimal('0.00')
    num_transacciones = agg_ventas.get('num_transacciones') or 0

    agg_unidades = VentaDetalle.objects.filter(venta__in=ventas_qs).aggregate(total_unidades=Sum('cantidad'))
    total_unidades = agg_unidades.get('total_unidades') or 0

    agg_cmv = VentaDetalle.objects.filter(venta__in=ventas_qs).aggregate(
        cmv=Sum(F('cantidad') * F('producto__precio_compra'))
    )
    cmv_val = agg_cmv.get('cmv') or 0
    cmv = Decimal(str(cmv_val))
    
    ganancia_bruta = ingreso_total - cmv
    margen = (ganancia_bruta / ingreso_total * 100) if ingreso_total > 0 else Decimal('0.00')
    ticket_promedio = (ingreso_total / num_transacciones) if num_transacciones > 0 else Decimal('0.00')
    unidades_promedio = (total_unidades / num_transacciones) if num_transacciones > 0 else 0
    
    best_selling = VentaDetalle.objects.filter(venta__in=ventas_qs) \
                        .values('producto__nombre') \
                        .annotate(total_cantidad=Sum('cantidad')) \
                        .order_by('-total_cantidad') \
                        .first()
    best_selling_product = best_selling['producto__nombre'] if best_selling else "N/A"
    best_selling_quantity = best_selling['total_cantidad'] if best_selling else 0

    sales_by_payment_type = Venta.objects.filter(
        fecha__gte=fecha_inicio, fecha__lte=fecha_fin
    ).values('forma_pago').annotate(
        total_monto=Sum('total')
    )
    sales_by_payment = []
    sales_by_payment_chart = []
    for item in sales_by_payment_type:
        monto = item['total_monto'] or 0
        sales_by_payment.append({
            'forma_pago': item['forma_pago'],
            'total_monto': "$" + format_clp(monto)
        })
        sales_by_payment_chart.append({
            'forma_pago': item['forma_pago'],
            'total_monto': float(monto)
        })
    
    filtro_top = request.GET.get('top', 10)
    try:
        filtro_top = int(filtro_top)
    except ValueError:
        filtro_top = 10
    
    top_selling_products = VentaDetalle.objects.filter(
        venta__fecha__gte=fecha_inicio, venta__fecha__lte=fecha_fin
    ).values('producto__nombre').annotate(
        total_cantidad=Sum('cantidad')
    ).order_by('-total_cantidad')[:filtro_top]

    if ingreso_total > 0:
        ingreso_sin_iva = (ingreso_total / Decimal('1.19')).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
        iva_total_calc = ingreso_total - ingreso_sin_iva
    else:
        ingreso_sin_iva = Decimal('0.00')
        iva_total_calc = Decimal('0.00')
    ganancia_liquida = ganancia_bruta

    context = {
        'ingreso_total': "$" + format_clp(ingreso_total),
        'ingreso_total_sin_iva': "$" + format_clp(ingreso_sin_iva),
        'iva_total': "$" + format_clp(iva_total_calc),
        'ganancia_bruta': "$" + format_clp(ganancia_bruta),
        'ganancia_liquida': "$" + format_clp(ganancia_liquida),
        'costo_total': "$" + format_clp(cmv),
        'margen': format_clp(margen) + "%",
        'num_transacciones': num_transacciones,
        'ticket_promedio': "$" + format_clp(ticket_promedio),
        'unidades_promedio': format_clp(unidades_promedio),
        'best_selling_product': best_selling_product,
        'best_selling_quantity': best_selling_quantity,
        'sales_by_payment': sales_by_payment,
        'sales_by_payment_chart': sales_by_payment_chart,
        'top_selling_products': list(top_selling_products),
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
        'filtro_top_actual': filtro_top,
    }
    
    return render(request, 'reports/advanced_reports.html', context)

@login_required
def caja_report(request, caja_id):
    """
    Vista para mostrar el detalle de una caja cerrada usando el template 'reporte_caja.html'.
    """
    caja = get_object_or_404(AperturaCierreCaja, id=caja_id)
    caja.formatted_efectivo_inicial = "$" + format_clp(caja.efectivo_inicial or 0)
    caja.formatted_total_ventas_debito = "$" + format_clp(caja.total_ventas_debito or 0)
    caja.formatted_total_ventas_credito = "$" + format_clp(caja.total_ventas_credito or 0)
    caja.formatted_total_ventas_efectivo = "$" + format_clp(caja.total_ventas_efectivo or 0)
    caja.formatted_vuelto_entregado = "$" + format_clp(caja.vuelto_entregado or 0)
    caja.formatted_efectivo_final = "$" + format_clp(caja.efectivo_final or 0)
    caja.formatted_ventas_totales = "$" + format_clp(caja.ventas_totales or 0)
    
    return render(request, 'reports/reporte_caja.html', {'caja': caja})

