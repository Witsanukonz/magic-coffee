// 1) ปฏิสัมพันธ์พื้นฐานร่วมกัน: เมนูพับ, sidebar และกล่องข้อความ.
document.querySelectorAll('[data-toggle]').forEach(button => {
  button.addEventListener('click', () => {
    const target = document.getElementById(button.dataset.toggle);
    target.hidden = !target.hidden;
    button.setAttribute('aria-expanded', String(!target.hidden));
  });
});
document.querySelector('[data-sidebar]')?.addEventListener('click', event => {
  const button = event.currentTarget;
  const open = document.body.classList.toggle('sidebar-open');
  button.setAttribute('aria-expanded', String(open));
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    document.body.classList.remove('sidebar-open');
    document.querySelector('[data-sidebar]')?.setAttribute('aria-expanded', 'false');
  }
});
document.querySelectorAll('[data-dismiss]').forEach(button => button.addEventListener('click', () => button.parentElement.remove()));
const money = amount => `฿${Number(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

// 2) ตะกร้า: คำนวณราคาหน้าจอทันที แล้วบันทึกจำนวนจริงผ่าน API.
const refreshCartTotals = () => {
  const forms = [...document.querySelectorAll('.cart-quantity-form')];
  let total = 0;
  let itemCount = 0;
  forms.forEach(form => {
    const input = form.querySelector('input[type="number"][name="quantity"]');
    const quantity = Number(input?.value) || 0;
    const price = Number(form.dataset.price) || 0;
    total += quantity * price;
    itemCount += quantity;
    form.closest('.cart-item')?.querySelector('[data-line-total]')?.replaceChildren(money(quantity * price));
    form.querySelector('[data-quantity="-1"]')?.toggleAttribute('disabled', quantity <= Number(input?.min || 1));
    form.querySelector('[data-quantity="1"]')?.toggleAttribute('disabled', quantity >= Number(input?.max || Infinity));
  });
  document.querySelectorAll('[data-order-total]').forEach(totalNode => totalNode.replaceChildren(money(total)));
  document.querySelectorAll('[data-order-item-count]').forEach(countNode => countNode.replaceChildren(`${itemCount} ITEM${itemCount === 1 ? '' : 'S'}`));
};
document.querySelectorAll('[data-quantity]').forEach(button => button.addEventListener('click', () => {
  const input = button.closest('form')?.querySelector('input[type="number"][name="quantity"]');
  if (!input) return;
  const previousQuantity = Number(input.value) || Number(input.min || 1);
  input.value = Math.max(Number(input.min || 1), Math.min(Number(input.max || 999), (Number(input.value) || 1) + Number(button.dataset.quantity)));
  refreshCartTotals();
  if (button.closest('.cart-quantity-form')) saveCartQuantity(button.closest('.cart-quantity-form'), previousQuantity);
}));
const saveCartQuantity = async (form, previousQuantity) => {
  if (form.dataset.saving === 'true') return;
  const input = form.querySelector('input[type="number"][name="quantity"]');
  const error = form.parentElement?.querySelector('[data-cart-error]');
  form.dataset.saving = 'true';
  form.querySelectorAll('[data-quantity]').forEach(button => { button.disabled = true; });
  if (error) error.hidden = true;
  try {
    const response = await fetch(form.action, {
      method: 'POST', credentials: 'same-origin', headers: { Accept: 'application/json' }, body: new FormData(form),
    });
    if (!response.ok) throw new Error('Unable to update this item.');
    const cart = await response.json();
    input.value = cart.quantity;
    input.defaultValue = String(cart.quantity);
    form.closest('.cart-item')?.querySelector('[data-line-total]')?.replaceChildren(money(cart.line_total));
    document.querySelectorAll('[data-order-total]').forEach(node => node.replaceChildren(money(cart.cart_total)));
    document.querySelectorAll('[data-order-item-count]').forEach(node => node.replaceChildren(`${cart.cart_count} ITEM${cart.cart_count === 1 ? '' : 'S'}`));
  } catch (_) {
    input.value = previousQuantity;
    if (error) { error.textContent = 'Could not update quantity. Please try again.'; error.hidden = false; }
  } finally {
    form.dataset.saving = 'false';
    refreshCartTotals();
  }
};
document.querySelectorAll('.cart-quantity-form input[type="number"]').forEach(input => input.addEventListener('change', () => {
  const previousQuantity = Number(input.defaultValue) || Number(input.min || 1);
  input.value = Math.max(Number(input.min || 1), Math.min(Number(input.max || 999), Number(input.value) || Number(input.min || 1)));
  refreshCartTotals();
  saveCartQuantity(input.closest('.cart-quantity-form'), previousQuantity);
}));
document.querySelectorAll('.cart-quantity-form').forEach(form => form.addEventListener('submit', event => {
  event.preventDefault();
  const input = form.querySelector('input[type="number"][name="quantity"]');
  saveCartQuantity(form, Number(input?.defaultValue) || Number(input?.min || 1));
}));

// 3) แต้มสะสม: เช็กสิทธิ์จากเบอร์โทร และซ่อนตัวเลือกกาแฟฟรีหากยังไม่ครบเงื่อนไข.
const loyaltyForm = document.querySelector('[data-loyalty-status-url]');
const loyaltyPhone = loyaltyForm?.querySelector('#id_phone');
const loyaltyReward = loyaltyForm?.querySelector('[data-loyalty-reward]');
const loyaltyMessage = loyaltyForm?.querySelector('[data-loyalty-message]');
const loyaltyHeading = loyaltyForm?.querySelector('[data-loyalty-heading]');
let loyaltyLookupTimer;
const checkLoyaltyReward = async () => {
  if (!loyaltyForm || !loyaltyPhone || !loyaltyReward) return;
  const digits = loyaltyPhone.value.replace(/\D/g, '');
  if (digits.length < 8) {
    loyaltyReward.hidden = true;
    const rewardSelect = loyaltyReward.querySelector('select');
    if (rewardSelect) rewardSelect.value = '';
    if (loyaltyHeading) loyaltyHeading.textContent = 'BUY 10, GET 1 FREE';
    if (loyaltyMessage) loyaltyMessage.textContent = 'Enter your phone number to check for a free coffee reward.';
    return;
  }
  try {
    const response = await fetch(loyaltyForm.dataset.loyaltyStatusUrl, {
      method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': loyaltyForm.querySelector('[name=csrfmiddlewaretoken]').value },
      body: new URLSearchParams({ phone: loyaltyPhone.value }),
    });
    if (!response.ok) throw new Error('Loyalty check failed.');
    const loyalty = await response.json();
    loyaltyReward.hidden = !loyalty.eligible;
    if (!loyalty.eligible) {
      const rewardSelect = loyaltyReward.querySelector('select');
      if (rewardSelect) rewardSelect.value = '';
    }
    if (loyaltyHeading) loyaltyHeading.textContent = loyalty.eligible ? 'FREE COFFEE UNLOCKED' : `${loyalty.visits_remaining} VISIT${loyalty.visits_remaining === 1 ? '' : 'S'} TO GO`;
    if (loyaltyMessage) loyaltyMessage.textContent = loyalty.eligible
      ? `${loyalty.reward_balance} free coffee reward available. Choose a coffee below to use it.`
      : 'Complete 10 purchases with this phone number to unlock a free coffee.';
  } catch (_) {
    loyaltyReward.hidden = true;
    if (loyaltyMessage) loyaltyMessage.textContent = 'We could not check rewards right now. You can still place your order.';
  }
};
if (loyaltyPhone) loyaltyPhone.addEventListener('input', () => {
  clearTimeout(loyaltyLookupTimer);
  loyaltyLookupTimer = window.setTimeout(checkLoyaltyReward, 350);
});

// 4) ลูกค้า: polling สถานะออเดอร์เพื่อให้หน้า My Order อัปเดตเอง.
const orderRanks = { pending: 1, preparing: 2, ready: 3, completed: 4 };
const refreshLiveOrder = (container, order) => {
  if (!order.status) return;
  if (order.loyalty) {
    container.querySelectorAll('[data-loyalty-visits]').forEach(node => { node.textContent = `${order.loyalty.completed_purchases} COMPLETED VISITS`; });
    container.querySelectorAll('[data-loyalty-rewards]').forEach(node => { node.textContent = order.loyalty.reward_balance; });
  }
  if (container.dataset.orderStatus === order.status) return;
  container.dataset.orderStatus = order.status;
  container.querySelectorAll('[data-order-badge]').forEach(badge => {
    badge.className = `badge ${order.status}`;
    badge.textContent = order.display;
  });
  container.querySelectorAll('[data-order-tracking-status]').forEach(status => { status.textContent = order.message; });
  container.querySelectorAll('[data-status-step]').forEach(step => {
    const rank = orderRanks[step.dataset.statusStep];
    step.classList.toggle('done', Boolean(rank && orderRanks[order.status] >= rank));
  });
  container.classList.remove('status-updated');
  void container.offsetWidth;
  container.classList.add('status-updated');
};
const pollLiveOrders = async () => {
  if (document.hidden) return;
  await Promise.all([...document.querySelectorAll('[data-live-order-url]')].map(async container => {
    try {
      const response = await fetch(container.dataset.liveOrderUrl, { credentials: 'same-origin', cache: 'no-store' });
      if (response.ok) refreshLiveOrder(container, await response.json());
    } catch (_) { /* A brief network failure should not interrupt ordering. */ }
  }));
};
if (document.querySelector('[data-live-order-url]')) {
  window.setInterval(pollLiveOrders, 5000);
  document.addEventListener('visibilitychange', pollLiveOrders);
}

// 5) แอดมิน: โหลด Kanban board ใหม่เพื่อให้ออเดอร์เข้ามาโดยไม่ต้องรีเฟรชหน้า.
const adminOrderContainers = [...document.querySelectorAll('[data-admin-orders-url]')];
if (adminOrderContainers.length) {
  const knownAdminOrderIds = new Set([...document.querySelectorAll('[data-order-id]')].map(order => order.dataset.orderId));
  const pollAdminOrders = async () => {
    if (document.hidden) return;
    await Promise.all(adminOrderContainers.map(async container => {
      try {
        const response = await fetch(container.dataset.adminOrdersUrl, { credentials: 'same-origin', cache: 'no-store' });
        if (!response.ok) return;
        const markup = await response.text();
        const preview = document.createElement('template');
        preview.innerHTML = markup;
        const incomingCards = [...preview.content.querySelectorAll('[data-order-id]')];
        const newCards = incomingCards.filter(card => !knownAdminOrderIds.has(card.dataset.orderId));
        incomingCards.forEach(card => knownAdminOrderIds.add(card.dataset.orderId));
        container.innerHTML = markup;
      } catch (_) { /* The next poll restores live data after a temporary network issue. */ }
    }));
  };
  window.setInterval(pollAdminOrders, 2000);
  document.addEventListener('visibilitychange', pollAdminOrders);
}

// 6) แอดมิน: แสดง stock alerts ที่ sidebar และ badge ของออเดอร์ใหม่บน Live Orders.
const adminAlertPanel = document.querySelector('[data-admin-alerts-url]');
if (adminAlertPanel) {
  const adminAlertList = adminAlertPanel.querySelector('[data-admin-alert-list]');
  const adminAlertCount = adminAlertPanel.querySelector('[data-admin-alert-count]');
  const liveOrderAlert = document.querySelector('[data-live-order-alert]');
  const knownAlertIds = new Set();
  let alertsLoaded = false;
  let previousPendingOrderCount = 0;
  const renderAdminAlerts = alerts => {
    adminAlertCount.textContent = alerts.length;
    if (!alerts.length) {
      const empty = document.createElement('p');
      empty.textContent = 'All clear for now.';
      adminAlertList.replaceChildren(empty);
      return;
    }
    const items = alerts.map(alert => {
      const link = document.createElement('a');
      link.href = alert.url;
      link.className = `sidebar-alert sidebar-alert-${alert.kind}`;
      if (alertsLoaded && !knownAlertIds.has(alert.id)) link.classList.add('sidebar-alert-arrived');
      const title = document.createElement('strong');
      title.textContent = alert.title;
      const detail = document.createElement('small');
      detail.textContent = alert.detail;
      link.append(title, detail);
      return link;
    });
    alerts.forEach(alert => knownAlertIds.add(alert.id));
    adminAlertList.replaceChildren(...items);
  };
  const pollAdminAlerts = async () => {
    if (document.hidden) return;
    try {
      const response = await fetch(adminAlertPanel.dataset.adminAlertsUrl, { credentials: 'same-origin', cache: 'no-store' });
      if (response.ok) {
        const payload = await response.json();
        renderAdminAlerts(payload.alerts);
        if (liveOrderAlert) {
          liveOrderAlert.textContent = payload.pending_order_count;
          liveOrderAlert.hidden = payload.pending_order_count === 0;
          if (alertsLoaded && payload.pending_order_count > previousPendingOrderCount) {
            liveOrderAlert.classList.remove('live-order-alert-arrived');
            void liveOrderAlert.offsetWidth;
            liveOrderAlert.classList.add('live-order-alert-arrived');
          }
        }
        previousPendingOrderCount = payload.pending_order_count;
      }
      alertsLoaded = true;
    } catch (_) { /* Alerts refresh on the next poll after a short network interruption. */ }
  };
  pollAdminAlerts();
  window.setInterval(pollAdminAlerts, 4000);
  document.addEventListener('visibilitychange', pollAdminAlerts);
}

// 7) ยูทิลิตีหน้าแอดมิน: preview รูป, confirm ลบ และ quick-order dialog.
document.querySelectorAll('[data-preview]').forEach(input => {
  let objectUrl;
  input.addEventListener('change', () => {
    const image = document.getElementById(input.dataset.preview);
    const file = input.files[0];
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
      input.setCustomValidity('Choose a JPG, PNG, or WebP image up to 5 MB.');
      input.reportValidity();
      return;
    }
    input.setCustomValidity('');
    objectUrl = URL.createObjectURL(file);
    image.src = objectUrl;
    image.hidden = false;
  });
});
const dialog = document.getElementById('delete-dialog');
document.querySelectorAll('[data-delete-url]').forEach(button => button.addEventListener('click', () => {
  document.getElementById('delete-form').action = button.dataset.deleteUrl;
  document.getElementById('delete-description').textContent = `Delete “${button.dataset.deleteName}”? This action cannot be undone.`;
  dialog.showModal();
}));
document.querySelector('[data-close-dialog]')?.addEventListener('click', () => dialog.close());
dialog?.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
document.querySelectorAll('[data-quick-open]').forEach(button => button.addEventListener('click', () => {
  document.getElementById(button.dataset.quickOpen)?.showModal();
}));
document.querySelectorAll('[data-quick-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog')?.close()));
document.querySelectorAll('.quick-order-dialog').forEach(quickDialog => quickDialog.addEventListener('click', event => {
  if (event.target === quickDialog) quickDialog.close();
}));
document.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => {
  const button = form.querySelector('[data-submit-once]');
  if (button) { button.disabled = true; button.textContent = 'PLEASE WAIT…'; }
}));
