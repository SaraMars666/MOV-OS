from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import get_user_model

from tests.factories import (
	create_user, create_sucursal, create_product,
	open_caja, close_caja, make_sale
)
from cashier.models import Venta, AperturaCierreCaja
from django.db.models import Sum

User = get_user_model()


class CashierFlowTests(TestCase):
	def setUp(self):
		self.sucursal = create_sucursal("Sucursal Central")
		self.user_admin = create_user("admin_user", is_staff=True)
		self.user_cajero = create_user("cajero_user", is_staff=False)
		self.prod_a = create_product("PX1", "Producto X", precio_compra=Decimal('1000'), precio_venta=Decimal('2500'))
		self.prod_b = create_product("PY1", "Producto Y", precio_compra=Decimal('700'), precio_venta=Decimal('2000'))

	def test_open_sale_close_caja_flow(self):
		caja = open_caja(self.user_admin, self.sucursal, efectivo_inicial=Decimal('5000'))
		self.assertEqual(caja.estado, 'abierta')
		v1 = make_sale(self.user_admin, self.sucursal, [(self.prod_a, 2), (self.prod_b, 1)], forma_pago='efectivo', caja=caja)
		v2 = make_sale(self.user_admin, self.sucursal, [(self.prod_b, 3)], forma_pago='debito', caja=caja)
		self.assertGreater(v1.total, 0)
		self.assertGreater(v2.total, 0)
		close_caja(caja)
		caja.refresh_from_db()
		self.assertEqual(caja.estado, 'cerrada')
		total_ventas = sum(v.total for v in Venta.objects.filter(caja=caja))
		self.assertEqual(caja.ventas_totales, total_ventas)

	def test_ranking_cajeros_basic(self):
		caja1 = open_caja(self.user_admin, self.sucursal)
		# Solo una caja abierta por sucursal (constraint); ventas de cajero_user sin caja propia si no se puede abrir otra
		make_sale(self.user_admin, self.sucursal, [(self.prod_a, 1)], caja=caja1)
		make_sale(self.user_admin, self.sucursal, [(self.prod_b, 2)], caja=caja1)
		close_caja(caja1)
		self.client.force_login(self.user_admin)
		fi = (timezone.now() - timezone.timedelta(days=2)).strftime('%Y-%m-%d')
		ff = timezone.now().strftime('%Y-%m-%d')
		resp = self.client.get('/reports/advanced/data/', {
			'fecha_inicio': fi,
			'fecha_fin': ff
		})
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertIn('ranking_cajeros', data)
		self.assertTrue(len(data['ranking_cajeros']) >= 1)

	def test_permission_reports_denied_for_non_staff(self):
		caja = open_caja(self.user_cajero, self.sucursal)
		make_sale(self.user_cajero, self.sucursal, [(self.prod_a, 1)], caja=caja)
		self.client.force_login(self.user_cajero)
		resp = self.client.get('/reports/advanced/', follow=False)
		self.assertNotEqual(resp.status_code, 200, "Un usuario no staff no debería ver reports avanzados")

	def test_efectivo_final_calculation(self):
		# Abrir caja con efectivo inicial, crear ventas en efectivo y con tarjeta, cerrar caja vía endpoint
		caja = open_caja(self.user_admin, self.sucursal, efectivo_inicial=Decimal('10000'))
		# Venta en efectivo 1
		v1 = make_sale(self.user_admin, self.sucursal, [(self.prod_a, 2)], forma_pago='efectivo', caja=caja)
		# Venta en efectivo 2 (con vuelto simulado por total > cliente_paga handled by view, but here we set total directly)
		v2 = make_sale(self.user_admin, self.sucursal, [(self.prod_b, 1)], forma_pago='efectivo', caja=caja)
		# Venta en tarjeta (no afecta efectivo final)
		v3 = make_sale(self.user_admin, self.sucursal, [(self.prod_b, 1)], forma_pago='debito', caja=caja)
		self.client.force_login(self.user_admin)
		resp = self.client.post('/cashier/cerrar_caja/', data='{"caja_id": %d}' % caja.id, content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		caja.refresh_from_db()
		# Calcular ventas en efectivo esperadas
		expected_ventas_efectivo = Venta.objects.filter(caja=caja, forma_pago='efectivo').aggregate(total=Sum('total'))['total'] or Decimal('0.00')
		expected_efectivo_final = (caja.efectivo_inicial or Decimal('0.00')) + expected_ventas_efectivo
		self.assertEqual(caja.efectivo_final, expected_efectivo_final)
