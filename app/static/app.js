const productList = document.querySelector("#product-list");
const feedback = document.querySelector("#feedback");
const createForm = document.querySelector("#create-form");
const editDialog = document.querySelector("#edit-dialog");
const editForm = document.querySelector("#edit-form");
const editFeedback = document.querySelector("#edit-feedback");
const apiStatus = document.querySelector("#api-status");
const currency = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 2,
});

let products = [];

function showFeedback(message, type = "") {
  feedback.textContent = message;
  feedback.className = `feedback ${type}`.trim();
}

function setEmptyRow(message) {
  productList.replaceChildren();
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 5;
  cell.className = "empty-state";
  cell.textContent = message;
  row.append(cell);
  productList.append(row);
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = `Error ${response.status}: no se pudo completar la operación.`;
    try {
      const body = await response.json();
      if (body.detail) message = body.detail;
    } catch {
      // Mantiene el mensaje HTTP si la respuesta no contiene JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) return null;
  return response.json();
}

function updateSummary() {
  document.querySelector("#product-count").textContent = products.length;
  document.querySelector("#inventory-value").textContent = currency.format(
    products.reduce((sum, product) => sum + product.price * product.quantity, 0),
  );
  document.querySelector("#low-stock-count").textContent = products.filter(
    (product) => product.quantity <= 5,
  ).length;
}

function renderProducts() {
  const query = document.querySelector("#search-input").value.trim().toLocaleLowerCase();
  const filteredProducts = products.filter((product) =>
    product.name.toLocaleLowerCase().includes(query),
  );

  updateSummary();
  if (!filteredProducts.length) {
    setEmptyRow(products.length ? "No hay productos que coincidan con la búsqueda." : "Todavía no hay productos en el inventario.");
    return;
  }

  productList.replaceChildren();
  for (const product of filteredProducts) {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    const name = document.createElement("div");
    name.className = "product-name";
    name.textContent = product.name;
    const id = document.createElement("div");
    id.className = "product-id";
    id.textContent = `ID #${product.id}`;
    nameCell.append(name, id);

    const priceCell = document.createElement("td");
    priceCell.textContent = currency.format(product.price);

    const quantityCell = document.createElement("td");
    quantityCell.textContent = product.quantity;

    const statusCell = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = "stock-badge";
    if (product.quantity === 0) {
      badge.classList.add("out");
      badge.textContent = "Agotado";
    } else if (product.quantity <= 5) {
      badge.classList.add("low");
      badge.textContent = "Stock bajo";
    } else {
      badge.textContent = "En stock";
    }
    statusCell.append(badge);

    const actionsCell = document.createElement("td");
    const actions = document.createElement("div");
    actions.className = "row-actions";
    const editButton = document.createElement("button");
    editButton.className = "icon-button";
    editButton.type = "button";
    editButton.setAttribute("aria-label", `Editar ${product.name}`);
    editButton.title = "Editar";
    editButton.textContent = "✎";
    editButton.addEventListener("click", () => openEditDialog(product));
    const deleteButton = document.createElement("button");
    deleteButton.className = "icon-button delete";
    deleteButton.type = "button";
    deleteButton.setAttribute("aria-label", `Eliminar ${product.name}`);
    deleteButton.title = "Eliminar";
    deleteButton.textContent = "×";
    deleteButton.addEventListener("click", () => deleteProduct(product));
    actions.append(editButton, deleteButton);
    actionsCell.append(actions);

    row.append(nameCell, priceCell, quantityCell, statusCell, actionsCell);
    productList.append(row);
  }
}

async function loadProducts() {
  showFeedback("");
  const refreshButton = document.querySelector("#refresh-products");
  refreshButton.disabled = true;
  try {
    const response = await request("/items");
    products = Object.entries(response).map(([id, item]) => ({
      id: Number(id),
      ...item,
    }));
    apiStatus.classList.remove("offline");
    apiStatus.lastChild.textContent = " API conectada";
    renderProducts();
  } catch (error) {
    products = [];
    apiStatus.classList.add("offline");
    apiStatus.lastChild.textContent = " API no disponible";
    updateSummary();
    setEmptyRow("No se pudieron cargar los productos.");
    showFeedback(error.message);
  } finally {
    refreshButton.disabled = false;
  }
}

function getFormPayload(form) {
  const formData = new FormData(form);
  return {
    name: formData.get("name").trim(),
    price: Number(formData.get("price")),
    quantity: Number(formData.get("quantity")),
  };
}

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = createForm.querySelector('button[type="submit"]');
  button.disabled = true;
  showFeedback("");
  try {
    await request("/items", {
      method: "POST",
      body: JSON.stringify(getFormPayload(createForm)),
    });
    createForm.reset();
    await loadProducts();
    showFeedback("Producto agregado correctamente.", "success");
  } catch (error) {
    showFeedback(error.message);
  } finally {
    button.disabled = false;
  }
});

function openEditDialog(product) {
  editForm.elements.id.value = product.id;
  editForm.elements.name.value = product.name;
  editForm.elements.price.value = product.price;
  editForm.elements.quantity.value = product.quantity;
  editFeedback.textContent = "";
  editFeedback.className = "feedback";
  editDialog.showModal();
}

async function deleteProduct(product) {
  if (!window.confirm(`¿Eliminar "${product.name}" del inventario?`)) return;
  showFeedback("");
  try {
    await request(`/items/${product.id}`, { method: "DELETE" });
    await loadProducts();
    showFeedback("Producto eliminado.", "success");
  } catch (error) {
    showFeedback(error.message);
  }
}

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = editForm.querySelector('button[type="submit"]');
  button.disabled = true;
  editFeedback.textContent = "";
  const id = editForm.elements.id.value;
  try {
    await request(`/items/${id}`, {
      method: "PATCH",
      body: JSON.stringify(getFormPayload(editForm)),
    });
    editDialog.close();
    await loadProducts();
    showFeedback("Cambios guardados correctamente.", "success");
  } catch (error) {
    editFeedback.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#search-input").addEventListener("input", renderProducts);
document.querySelector("#refresh-products").addEventListener("click", loadProducts);
document.querySelector("#close-dialog").addEventListener("click", () => editDialog.close());
document.querySelector("#cancel-edit").addEventListener("click", () => editDialog.close());
editDialog.addEventListener("click", (event) => {
  if (event.target === editDialog) editDialog.close();
});
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") loadProducts();
});

loadProducts();
