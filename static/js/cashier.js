document.addEventListener("DOMContentLoaded", () => {
    // Referencias de elementos generales
    const cerrarCajaBtn = document.getElementById("close-cash-button");
    const confirmarCompraButton = document.getElementById("confirmar-compra");
    const cantidadPagadaInput = document.getElementById("cantidad_pagada");
    const vueltoElement = document.getElementById("vuelto");
    const totalPriceElement = document.getElementById("total-price");
    const cartItemsContainer = document.getElementById("cart-items");
    const searchButton = document.getElementById("product-search-button");
    const searchInput = document.getElementById("product-search-input");
    const resultsList = document.getElementById("product-search-results");
    const barcodeInput = document.getElementById("barcode-input");

    // Referencias a inputs ocultos y contenedores extra
    const saleTypeInput = document.getElementById("sale-type");
    const paymentHiddenInput = document.getElementById("payment-method");
    const numeroTransaccionInput = document.getElementById("numero_transaccion");
    const transactionInfoContainer = document.getElementById("transaction-info");
    const bancoInfoContainer = document.getElementById("banco-info");
    const bancoInput = document.getElementById("banco");

    // Referencia al botón del modal de confirmación
    const confirmAndPrintBtn = document.getElementById("confirmAndPrintBtn");
    const confirmModalElement = document.getElementById("confirmPurchaseModal");
    const confirmModal = new bootstrap.Modal(confirmModalElement);

    // Variables para almacenar selección y carrito
    let tipoVenta = "boleta";
    let formaPago = "efectivo";
    let carrito = new Map();
    let totalCarrito = 0;

    // Función para formatear moneda (sin decimales)
    function formatChileanCurrency(number) {
        return number.toLocaleString('es-CL', { maximumFractionDigits: 0 });
    }

    // Obtención del token CSRF
    function getCSRFToken() {
        return document.cookie.split("; ").find(row => row.startsWith("csrftoken="))?.split("=")[1] || null;
    }

    // Función para mostrar mensajes Toast
    function showToast(message, type = "success") {
        const toastContainer = document.getElementById("toast-container") || (() => {
            const tc = document.createElement("div");
            tc.id = "toast-container";
            tc.style.position = "fixed";
            tc.style.top = "20px";
            tc.style.right = "20px";
            tc.style.zIndex = "1050";
            document.body.appendChild(tc);
            return tc;
        })();

        const toastId = `toast-${Date.now()}`;
        toastContainer.innerHTML += `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body fs-6">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        const toastElement = document.getElementById(toastId);
        new bootstrap.Toast(toastElement, { delay: 4000 }).show();
        setTimeout(() => toastElement.remove(), 4500);
    }

    // Función para calcular el vuelto:
    // Efectivo: si el campo pago está vacío, se muestra -total; de lo contrario, (pago - total).
    // Otros métodos: siempre 0.
    function calcularVuelto() {
        if (formaPago === "efectivo") {
            if (cantidadPagadaInput.value.trim() === "") {
                vueltoElement.textContent = `-$${formatChileanCurrency(totalCarrito)}`;
            } else {
                const pagado = parseFloat(cantidadPagadaInput.value) || 0;
                const calculado = pagado - totalCarrito;
                vueltoElement.textContent = `$${formatChileanCurrency(calculado)}`;
            }
        } else {
            vueltoElement.textContent = "$0";
        }
    }
    cantidadPagadaInput.addEventListener("input", calcularVuelto);

    // Función de debounce para búsquedas
    function debounce(func, delay = 300) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), delay);
        };
    }

    // Búsqueda de productos
    async function searchProducts(query) {
        try {
            const res = await fetch(`/cashier/buscar-producto/?q=${query}`);
            const data = await res.json();
            resultsList.innerHTML = "";
            if (data.productos.length === 0) {
                resultsList.innerHTML = `<li class="list-group-item">No se encontraron productos.</li>`;
                return;
            }
            data.productos.forEach(p => {
                const li = document.createElement("li");
                li.className = "list-group-item d-flex justify-content-between align-items-center";
                li.innerHTML = `
                    <span>${p.nombre} - $${formatChileanCurrency(parseFloat(p.precio_venta))}</span>
                    <button class="btn btn-success btn-sm" data-id="${p.id}" data-nombre="${p.nombre}" data-precio="${p.precio_venta}">
                        <i class="fas fa-plus"></i>
                    </button>
                `;
                resultsList.appendChild(li);
            });
        } catch (err) {
            console.error(err);
            showToast("Error en la búsqueda.", "danger");
        }
    }
    searchButton.addEventListener("click", debounce(() => {
        const query = searchInput.value.trim();
        if (!query) return showToast("Ingresa un término de búsqueda.", "warning");
        searchProducts(query);
    }));
    searchInput.addEventListener("keydown", (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            const query = searchInput.value.trim();
            if (!query) return showToast("Ingresa un término de búsqueda.", "warning");
            searchProducts(query);
        }
    });
    resultsList.addEventListener("click", (e) => {
        if (e.target.closest("button")) {
            const button = e.target.closest("button");
            const { id, nombre, precio } = button.dataset;
            agregarAlCarrito(parseInt(id), nombre, parseFloat(precio));
        }
    });
    async function agregarAlCarrito(productoId, nombre, precio) {
        if (!productoId) return;
        try {
            const res = await fetch(`/cashier/agregar-al-carrito/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({ producto_id: productoId })
            });
            const data = await res.json();
            if (!res.ok) {
                showToast(data.error || "Error al agregar al carrito.", "danger");
                return;
            }
            const item = data.carrito.find(item => item.producto_id === productoId);
            if (item) {
                carrito.set(productoId, {
                    producto_id: item.producto_id,
                    nombre: item.nombre,
                    precio: item.precio,
                    cantidad: item.cantidad
                });
                actualizarCarrito();
                showToast("Producto agregado al carrito", "success");
            }
        } catch (err) {
            console.error("Error al agregar al carrito:", err);
            showToast("Error de conexión al agregar al carrito.", "danger");
        }
    }
    function actualizarCarrito() {
        cartItemsContainer.innerHTML = "";
        totalCarrito = 0;
        if (carrito.size === 0) {
            cartItemsContainer.innerHTML = `<tr><td colspan="4" class="text-center">No hay productos en el carrito.</td></tr>`;
        } else {
            carrito.forEach(({ producto_id, nombre, precio, cantidad }) => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${cantidad}</td>
                    <td>${nombre}</td>
                    <td>$${formatChileanCurrency(cantidad * precio)}</td>
                    <td>
                        <button class="btn btn-success btn-sm" data-id="${producto_id}" data-action="increment">+</button>
                        <button class="btn btn-danger btn-sm" data-id="${producto_id}" data-action="decrement">-</button>
                    </td>
                `;
                cartItemsContainer.appendChild(row);
            });
        }
        totalCarrito = Array.from(carrito.values()).reduce((acc, item) => acc + (item.cantidad * item.precio), 0);
        totalPriceElement.textContent = `$${formatChileanCurrency(totalCarrito)}`;
        if (["debito", "credito", "transferencia"].includes(formaPago)) {
            cantidadPagadaInput.value = totalCarrito;
        }
        calcularVuelto();
    }
    cartItemsContainer.addEventListener("click", (e) => {
        const targetButton = e.target.closest("button");
        if (!targetButton) return;
        const productoId = parseInt(targetButton.dataset.id);
        if (!productoId) return;
        const item = carrito.get(productoId);
        if (targetButton.dataset.action === "increment") {
            item.cantidad++;
        } else if (targetButton.dataset.action === "decrement") {
            item.cantidad--;
            if (item.cantidad <= 0) carrito.delete(productoId);
        }
        actualizarCarrito();
    });

    // --- Manejo de botones para Tipo de Venta ---
    document.querySelectorAll('[data-sale-type]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('[data-sale-type]').forEach(function(b) {
                b.classList.remove("btn-primary", "active");
                b.classList.add("btn-outline-primary");
            });
            this.classList.remove("btn-outline-primary");
            this.classList.add("btn-primary", "active");
            saleTypeInput.value = this.getAttribute('data-sale-type');
            tipoVenta = this.getAttribute('data-sale-type');
        });
    });

    // --- Manejo de botones para Forma de Pago ---
    document.querySelectorAll('[data-payment-method]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('[data-payment-method]').forEach(function(b) {
                b.classList.remove("btn-primary", "active");
                b.classList.add("btn-outline-primary");
            });
            this.classList.remove("btn-outline-primary");
            this.classList.add("btn-primary", "active");
            if (paymentHiddenInput) {
                paymentHiddenInput.value = this.getAttribute('data-payment-method');
            }
            formaPago = this.getAttribute('data-payment-method');

            if (["debito", "credito", "transferencia"].includes(formaPago)) {
                cantidadPagadaInput.value = totalCarrito;
                cantidadPagadaInput.readOnly = true;
                vueltoElement.textContent = "$0";
            } else if (formaPago === "efectivo") {
                cantidadPagadaInput.readOnly = false;
                if (cantidadPagadaInput.value.trim() === "") {
                    vueltoElement.textContent = `-$${formatChileanCurrency(totalCarrito)}`;
                }
            }

            if (["debito", "credito", "transferencia"].includes(formaPago)) {
                transactionInfoContainer.style.display = "block";
            } else {
                transactionInfoContainer.style.display = "none";
                if (numeroTransaccionInput) numeroTransaccionInput.value = "";
                if (bancoInput) bancoInput.value = "";
            }
            if (formaPago === "transferencia") {
                bancoInfoContainer.style.display = "block";
            } else {
                bancoInfoContainer.style.display = "none";
                if (bancoInput) bancoInput.value = "";
            }
            calcularVuelto();
        });
    });

    // Al hacer clic en "Confirmar Compra", se muestra el modal de confirmación
    confirmarCompraButton.addEventListener("click", () => {
        // Validaciones previas
        if (carrito.size === 0) {
            showToast("El carrito está vacío", "warning");
            return;
        }
        if (formaPago === "efectivo") {
            const pagado = parseFloat(cantidadPagadaInput.value) || 0;
            if (pagado < totalCarrito) {
                showToast("El monto pagado es insuficiente.", "warning");
                return;
            }
        }
        if (["debito", "credito", "transferencia"].includes(formaPago) && !numeroTransaccionInput.value.trim()) {
            showToast("Debe ingresar el número de transacción.", "error");
            return;
        }
        if (formaPago === "transferencia" && !bancoInput.value.trim()) {
            showToast("Debe ingresar el nombre del banco.", "error");
            return;
        }
        // Se muestra el modal para confirmar la compra
        confirmModal.show();
    });

    // Al confirmar en el modal, se efectúa la compra y se redirige (si hay reporte)
    confirmAndPrintBtn.addEventListener("click", async () => {
        try {
            const res = await fetch("/cashier/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({
                    carrito: Array.from(carrito.values()),
                    tipo_venta: tipoVenta,
                    forma_pago: formaPago,
                    cliente_paga: parseFloat(cantidadPagadaInput.value) || 0,
                    numero_transaccion: (["debito", "credito", "transferencia"].includes(formaPago)) ? numeroTransaccionInput.value.trim() : "",
                    banco: (formaPago === "transferencia") ? bancoInput.value.trim() : ""
                })
            });
            const data = await res.json();
            if (!res.ok || !data.success) {
                showToast(data.error || "Error al confirmar", "danger");
                return;
            }
            showToast("Compra confirmada con éxito", "success");
            // Limpia la variable local
            carrito.clear();
            actualizarCarrito();
            // Llama al endpoint para limpiar el carrito de la sesión
            await fetch("/cashier/limpiar_carrito/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken()
                }
            });
            confirmModal.hide();
            if (data.reporte_url) window.open(data.reporte_url, "_blank");
        } catch (err) {
            console.error("Error al confirmar compra:", err);
            showToast("Error al procesar la compra", "danger");
        }
    });

    // Cerrar Caja
    if (cerrarCajaBtn) {
        cerrarCajaBtn.addEventListener("click", async () => {
            try {
                const res = await fetch("/cashier/cerrar_caja/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                        "Content-Type": "application/json"
                    }
                });
                const data = await res.json();
                if (data.success && data.caja_id) {
                    showToast("Caja cerrada con éxito.", "success");
                    window.location.href = `/cashier/detalle-caja/${data.caja_id}/`;
                } else {
                    showToast(data.error || "Error al cerrar la caja.", "danger");
                }
            } catch (err) {
                showToast("Error al cerrar la caja", "danger");
            }
        });
    }

    // Al cerrar caja, solicitar confirmación
    if(cerrarCajaBtn) {
        cerrarCajaBtn.addEventListener("click", (e) => {
            if (!confirm("¿Estás seguro que deseas cerrar la caja?")) {
                e.preventDefault();
            } else {
                // Si la acción de cerrar caja se realiza mediante un fetch o redirección,
                // se continúa; de lo contrario, en caso de un formulario, se puede proceder.
                // Ejemplo: llamar a la función de cerrar caja.
            }
        });
    }

    // Escaneo de código de barras
    async function handleBarcodeScan() {
        const barcode = barcodeInput.value.trim();
        if (!barcode) return;
        try {
            const res = await fetch(`/cashier/buscar-producto/?q=${barcode}`);
            const data = await res.json();
            if (data.productos.length > 0) {
                const product = data.productos[0];
                agregarAlCarrito(product.id, product.nombre, parseFloat(product.precio_venta));
                barcodeInput.value = "";
            } else {
                showToast("Producto no encontrado. Intenta de nuevo.", "warning");
                barcodeInput.value = "";
            }
        } catch (err) {
            console.error(err);
            showToast("Error al buscar producto por código de barras.", "danger");
        }
    }
    barcodeInput.addEventListener("keydown", (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            handleBarcodeScan();
        }
    });

    // Inicialización en caso de carrito vacío
    if (carrito.size === 0) {
        cantidadPagadaInput.value = "";
        totalPriceElement.textContent = `$0`;
        vueltoElement.textContent = `$0`;
    }
});