from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.db.models import Q
from cashier.models import Venta, VentaDetalle, AperturaCierreCaja  
from auth_app.models import User
from django.utils.timezone import localtime, make_aware
import datetime
from django.shortcuts import render
from django.db.models import Sum, F, Count
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta



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
    # Obtener parámetros de filtrado desde GET
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    empleado_id = request.GET.get('empleado')
    page = request.GET.get('page', 1)

    # Obtener todas las ventas y ordenar por fecha descendente
    ventas = Venta.objects.all().order_by('-fecha')

    # Filtrar por rango de fechas si se proporcionan
    if fecha_inicio:
        try:
            fecha_inicio_obj = make_aware(datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d'))
            ventas = ventas.filter(fecha__gte=fecha_inicio_obj)
        except ValueError:
            ventas = Venta.objects.none()

    if fecha_fin:
        try:
            fecha_fin_obj = make_aware(datetime.datetime.strptime(fecha_fin, '%Y-%m-%d'))
            # Para incluir el día completo, se ajusta la fecha de fin al final del día
            fecha_fin_obj += datetime.timedelta(days=1, seconds=-1)
            ventas = ventas.filter(fecha__lte=fecha_fin_obj)
        except ValueError:
            ventas = Venta.objects.none()

    # Filtrar por empleado si se selecciona
    if empleado_id:
        try:
            empleado_id = int(empleado_id)
            ventas = ventas.filter(empleado_id=empleado_id)
        except ValueError:
            ventas = Venta.objects.none()

    # Configuración de la paginación
    paginator = Paginator(ventas, 8)
    sales_page = paginator.get_page(page)

    # Obtener la lista de empleados para el selector de filtrado
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
    # Obtener parámetros de filtrado desde GET
    id_caja_filtro = request.GET.get('id_caja')
    cajero_filtro = request.GET.get('cajero')
    fecha_inicio_filtro = request.GET.get('fecha_inicio')
    fecha_fin_filtro = request.GET.get('fecha_fin')
    page = request.GET.get('page', 1)

    # Definir las opciones de paginación
    per_page_options = [5, 10, 15, 20]
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    if per_page not in per_page_options:
        per_page = 10

    # Inicializar el queryset base
    cajas = AperturaCierreCaja.objects.all().order_by('-fecha_apertura')

    # Aplicar filtros
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

    # Configuración de la paginación
    paginator = Paginator(cajas, per_page)
    cash_page = paginator.get_page(page)

    # Calcular datos adicionales para cada caja
    for caja in cash_page:
        if caja.estado == 'cerrada':
            caja.vuelto_entregado = caja.vuelto_entregado or 0
            caja.efectivo_final = caja.efectivo_final or (
                caja.efectivo_inicial + caja.total_ventas_efectivo - caja.vuelto_entregado
            )

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
    """Reporte detallado de una venta específica"""
    try:
        # Obtener la venta
        venta = get_object_or_404(Venta, id=sale_id)
        
        # Obtener los detalles (productos) de esa venta
        # Usamos el related_name='detalles' definido en tu modelo VentaDetalle
        detalles = venta.detalles.all()

        return render(request, 'reports/sales_report.html', {'venta': venta, 'detalles': detalles})
    except Exception as e:
        # Manejo de errores más específico en producción
        return render(request, 'reports/sales_report.html', {
            'error': str(e),
            'venta': None,
            'detalles': None
        })
    
@login_required
def advanced_reports(request):
    """
    Genera reportes avanzados con filtros de tiempo y cantidad de productos.
    """
    # Lógica de filtros de tiempo
    filtro_tiempo = request.GET.get('filtro', 'mensual')
    fecha_inicio = timezone.now() - timedelta(days=30) 

    if filtro_tiempo == 'semanal':
        fecha_inicio = timezone.now() - timedelta(days=7)
    elif filtro_tiempo == 'anual':
        fecha_inicio = timezone.now() - timedelta(days=365)
    
    # Lógica para el filtro de cantidad de productos
    filtro_top = int(request.GET.get('top', 10))
    
    # 📊 Reporte 1: Productos más vendidos (por cantidad)
    top_selling_products = VentaDetalle.objects.filter(
        venta__fecha__gte=fecha_inicio
    ).values('producto__nombre').annotate(
        total_cantidad=Sum('cantidad')
    ).order_by('-total_cantidad')[:filtro_top]

    # 📈 Reporte 2: Productos con mayor ingreso (monto de venta)
    top_revenue_products = VentaDetalle.objects.filter(
        venta__fecha__gte=fecha_inicio
    ).values('producto__nombre').annotate(
        total_ingreso=Sum(F('cantidad') * F('producto__precio_venta'))
    ).order_by('-total_ingreso')[:filtro_top]

    # 💰 Reporte 3: Productos con mayor ganancia (ingreso - costo)
    top_profit_products = VentaDetalle.objects.filter(
        venta__fecha__gte=fecha_inicio
    ).values('producto__nombre').annotate(
        total_ganancia=Sum(F('cantidad') * (F('producto__precio_venta') - F('producto__precio_compra')))
    ).order_by('-total_ganancia')[:filtro_top]

    # 💳 Ventas por Tipo de Pago
    sales_by_payment_type = Venta.objects.filter(
        fecha__gte=fecha_inicio
    ).values('forma_pago').annotate(
        total_monto=Sum('total')
    )
    
    # Convertir a float para JavaScript
    for venta in sales_by_payment_type:
        venta['total_monto'] = float(venta['total_monto'])
    for producto in top_revenue_products:
        producto['total_ingreso'] = float(producto['total_ingreso'])
    for producto in top_profit_products:
        producto['total_ganancia'] = float(producto['total_ganancia'])

    context = {
        'top_selling_products': list(top_selling_products),
        'top_revenue_products': list(top_revenue_products),
        'top_profit_products': list(top_profit_products),
        'sales_by_payment_type': list(sales_by_payment_type),
        'filtro_actual': filtro_tiempo,
        'filtro_top_actual': filtro_top,
    }

    return render(request, 'reports/advanced_reports.html', context)

