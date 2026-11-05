import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { getOrderHistory } from "../api/history";
import { approveOrder, listAllOrders, rejectOrder } from "../api/orders";
import type { Order, OrderStatus } from "../api/types";
import { HistoryFeed } from "../components/HistoryFeed";
import { Modal } from "../components/Modal";
import { formatPrice, ORDER_STATUS_LABEL } from "../lib/format";

export function AdminOrdersPage() {
  const [status, setStatus] = useState<OrderStatus | "">("");
  const [orders, setOrders] = useState<Order[]>([]);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [historyOrder, setHistoryOrder] = useState<Order | null>(null);

  async function load(nextStatus: OrderStatus | "" = status) {
    setLoading(true);
    try {
      const result = await listAllOrders(nextStatus || undefined);
      setOrders(result.items);
      setTotalCount(result.total_orders_count);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить заявки");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function act(kind: "approve" | "reject", orderId: string) {
    setError("");
    try {
      let updated: Order;
      if (kind === "approve") {
        updated = await approveOrder(orderId);
      } else {
        updated = await rejectOrder(orderId);
      }
      setOrders((prev) =>
        prev.map((o) => (o.id === orderId ? { ...o, status: updated.status } : o)),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить заявку");
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Все заявки</h1>
          {totalCount !== null ? (
            <p className="muted">Всего создано заказов: {totalCount}</p>
          ) : null}
        </div>
        <select
          value={status}
          onChange={(event) => {
            const value = event.target.value as OrderStatus | "";
            setStatus(value);
            void load(value);
          }}
        >
          <option value="">Все статусы</option>
          <option value="CREATED">Созданы</option>
          <option value="APPROVED">Одобрены</option>
          <option value="REJECTED">Отклонены</option>
          <option value="CANCELLED">Отменены</option>
        </select>
      </div>
      {error ? <p className="error">{error}</p> : null}
      {loading ? <div className="skeleton" /> : null}
      {!loading && orders.length === 0 ? <div className="card empty">Заявок нет</div> : null}
      <div className="list">
        {orders.map((order) => (
          <article key={order.id} className="card row">
            <div className="row__main">
              <strong>{order.product_snapshot.name}</strong>
              <span className="muted">
                {order.quantity} шт. · {formatPrice(order.total_amount)} · {order.user_id}
              </span>
            </div>
            <div className="row__actions">
              <span className={`status status--${order.status}`}>
                {ORDER_STATUS_LABEL[order.status]}
              </span>
              <button
                type="button"
                className="btn btn--ghost btn--sm"
                onClick={() => setHistoryOrder(order)}
              >
                История
              </button>
              {order.status === "CREATED" ? (
                <>
                  <button type="button" className="btn btn--primary" onClick={() => void act("approve", order.id)}>
                    Ок
                  </button>
                  <button type="button" className="btn btn--ghost" onClick={() => void act("reject", order.id)}>
                    Отклонить
                  </button>
                </>
              ) : null}
            </div>
          </article>
        ))}
      </div>

      <Modal
        isOpen={!!historyOrder}
        onClose={() => setHistoryOrder(null)}
        title={historyOrder ? `История заказа #${historyOrder.id.slice(0, 8)}` : ""}
      >
        {historyOrder ? (
          <HistoryFeed
            key={historyOrder.id}
            fetchPage={useCallback(
              (cursor?: string | null) =>
                getOrderHistory(historyOrder.id, { limit: 10, last_event_id: cursor }),
              [historyOrder.id],
            )}
            emptyText="Событий по этому заказу пока нет"
          />
        ) : null}
      </Modal>
    </>
  );
}
