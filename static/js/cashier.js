document.addEventListener("DOMContentLoaded", () => {
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

    const tipoVentaInputs = document.querySelectorAll('input[name="sale-type"]');
    const formaPagoInputs = document.querySelectorAll('input[name="payment-method"]');

    let tipoVenta = "boleta";
    let formaPago = "efectivo";

    let carrito = new Map();
    let totalCarrito = 0;

    function getCSRFToken() {
        return document.cookie.split("; ").find(row => row.startsWith("csrftoken="))?.split("=")[1] || null;
    }

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

    function calcularVuelto() {
        const pagado = parseFloat(cantidadPagadaInput.value) || 0;
        const total = parseFloat(totalPriceElement.textContent.replace("$", "")) || 0;
        
        if (formaPago === "efectivo") {
            const vuelto = pagado - total;
            vueltoElement.textContent = `$${vuelto.toFixed(2)}`;
        } else {
            vueltoElement.textContent = `$0.00`;
        }
    }

    cantidadPagadaInput.addEventListener("input", calcularVuelto);

    function debounce(func, delay = 300) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), delay);
        };
    }

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
                    <span>${p.nombre} - $${p.precio_venta}</span>
                    <button class="btn btn-success btn-sm" 
                    data-id="${p.id}" data-nombre="${p.nombre}" data-precio="${p.precio_venta}">
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
            // Revisa el stock antes de agregar al carrito
            const res = await fetch(`/cashier/agregar-al-carrito/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({
                    producto_id: productoId
                })
            });

            const data = await res.json();
            if (!res.ok) {
                showToast(data.error || "Error al agregar al carrito.", "danger");
                return;
            }

            // Actualiza el carrito local con la respuesta del servidor
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
                    <td>$${(cantidad * precio).toFixed(2)}</td>
                    <td>
                        <button class="btn btn-success btn-sm" data-id="${producto_id}" data-action="increment">+</button>
                        <button class="btn btn-danger btn-sm" data-id="${producto_id}" data-action="decrement">-</button>
                    </td>
                `;
                cartItemsContainer.appendChild(row);
            });
        }

        totalCarrito = Array.from(carrito.values()).reduce((acc, item) => acc + (item.cantidad * item.precio), 0);
        totalPriceElement.textContent = `$${totalCarrito.toFixed(2)}`;
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

    tipoVentaInputs.forEach(input => {
        input.addEventListener("change", () => {
            tipoVenta = input.id;
        });
    });

    formaPagoInputs.forEach(input => {
        input.addEventListener("change", () => {
            formaPago = input.id;
            if (formaPago === "debito" || formaPago === "credito") {
                cantidadPagadaInput.value = totalCarrito.toFixed(2);
            } else {
                cantidadPagadaInput.value = "";
            }
            calcularVuelto();
        });
    });

    // 📌 CAMBIO CLAVE: Se elimina la ventana de confirmación para que la compra se procese inmediatamente
    confirmarCompraButton.addEventListener("click", async () => {
        if (carrito.size === 0) {
            showToast("El carrito está vacío", "warning");
            return;
        }

        if (formaPago === "efectivo" && parseFloat(cantidadPagadaInput.value) < totalCarrito) {
            showToast("El monto pagado es insuficiente.", "warning");
            return;
        }

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
                    cliente_paga: parseFloat(cantidadPagadaInput.value) || 0
                })
            });

            const data = await res.json();
            if (!res.ok || !data.success) {
                showToast(data.error || "Error al confirmar", "danger");
                return;
            }

            showToast("Compra confirmada con éxito", "success");
            carrito.clear();
            actualizarCarrito();

            // Abre el comprobante de forma instantánea
            if (data.reporte_url) window.open(data.reporte_url, "_blank");

        } catch (err) {
            console.error("Error al confirmar compra:", err);
            showToast("Error al procesar la compra", "danger");
        }
    });

    if (cerrarCajaBtn) {
        // 📌 CAMBIO CLAVE: Se elimina la ventana de confirmación para que el cierre de caja sea inmediato
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

    // 📌 NUEVA LÓGICA PARA ESCANEAR CÓDIGO DE BARRAS
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
    
    if (carrito.size === 0) {
        cantidadPagadaInput.value = "";
        totalPriceElement.textContent = `$0.00`;
        vueltoElement.textContent = `$0.00`;
    }
});
