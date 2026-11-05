import { FormEvent, useCallback, useState } from "react";
import {
  addUserFavourite,
  checkoutUser,
  clearUserCart,
  clearUserFavourites,
  getUserCart,
  getUserFavourites,
  getUserOrders,
} from "../api/admin";
import { getUserByEmail } from "../api/auth";
import { ApiError } from "../api/client";
import { getUserHistory } from "../api/history";
import type { Cart, Favourites, Order, User } from "../api/types";
import { HistoryFeed } from "../components/HistoryFeed";
import { formatPrice, ORDER_STATUS_LABEL, roleLabel } from "../lib/format";

export function AdminUserPage() {
  const [email, setEmail] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [favourites, setFavourites] = useState<Favourites | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [productId, setProductId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadRelated(id: string) {
    const [nextFavs, nextCart, nextOrders] = await Promise.all([
      getUserFavourites(id),
      getUserCart(id),
      getUserOrders(id),
    ]);
    setFavourites(nextFavs);
    setCart(nextCart);
    setOrders(nextOrders.items);
  }

  async function onLoad(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const nextUser = await getUserByEmail(email.trim());
      setUser(nextUser);
      await loadRelated(nextUser.id);
    } catch (err) {
      setUser(null);
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить пользователя");
    }
  }

  return (
    <>
      <h1>Пользователь</h1>
      <form className="card filters" onSubmit={onLoad} style={{ gridTemplateColumns: "1fr auto" }}>
        <label className="field">
          <span>Email пользователя</span>
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <button className="btn btn--primary" type="submit">
          Открыть
        </button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      {message ? <p className="ok">{message}</p> : null}
      {user ? (
        <>
          <p className="muted" style={{ marginBottom: 16 }}>
            {user.name} · {user.email} · {roleLabel(user.role)}
          </p>
          <div className="page-head">
            <h2>Избранное</h2>
            <button
              type="button"
              className="btn btn--danger"
              onClick={() =>
                void clearUserFavourites(user.id)
                  .then((value) => setFavourites(value))
                  .catch((err: unknown) =>
                    setError(err instanceof ApiError ? err.message : "Ошибка избранного"),
                  )
              }
            >
              Очистить
            </button>
          </div>
          <form
            className="card filters"
            style={{ gridTemplateColumns: "1fr auto" }}
            onSubmit={(event) => {
              event.preventDefault();
              void addUserFavourite(user.id, productId.trim())
                .then((value) => {
                  setFavourites(value);
                  setProductId("");
                })
                .catch((err: unknown) =>
                  setError(err instanceof ApiError ? err.message : "Не удалось добавить"),
                );
            }}
          >
            <label className="field">
              <span>ID товара</span>
              <input value={productId} onChange={(event) => setProductId(event.target.value)} />
            </label>
            <button className="btn btn--ghost" type="submit">
              В избранное
            </button>
          </form>
          <div className="list" style={{ marginBottom: 24 }}>
            {(favourites?.products ?? []).map((item) => (
              <article key={item.product_id} className="card row">
                <span>{item.product?.name ?? item.product_id}</span>
              </article>
            ))}
          </div>
          <div className="page-head">
            <h2>Корзина · {formatPrice(cart?.total_amount ?? "0")}</h2>
            <div className="row__actions">
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() =>
                  void checkoutUser(user.id)
                    .then((result) => {
                      setMessage(`Оформлено: ${result.total_orders}`);
                      return loadRelated(user.id);
                    })
                    .catch((err: unknown) =>
                      setError(err instanceof ApiError ? err.message : "Checkout не удался"),
                    )
                }
              >
                Checkout
              </button>
              <button
                type="button"
                className="btn btn--danger"
                onClick={() =>
                  void clearUserCart(user.id)
                    .then(setCart)
                    .catch((err: unknown) =>
                      setError(err instanceof ApiError ? err.message : "Ошибка корзины"),
                    )
                }
              >
                Очистить
              </button>
            </div>
          </div>
          <div className="list" style={{ marginBottom: 24 }}>
            {(cart?.items ?? []).map((item) => (
              <article key={item.product_id} className="card row">
                <span>
                  {item.product?.name ?? item.product_id} × {item.quantity}
                </span>
              </article>
            ))}
          </div>
          <h2>Заявки</h2>
          <div className="list" style={{ marginBottom: 24 }}>
            {orders.map((order) => (
              <article key={order.id} className="card row">
                <div className="row__main">
                  <strong>{order.product_snapshot.name}</strong>
                  <span className="muted">{formatPrice(order.total_amount)}</span>
                </div>
                <span className={`status status--${order.status}`}>
                  {ORDER_STATUS_LABEL[order.status]}
                </span>
              </article>
            ))}
          </div>

          <div style={{ marginTop: 24, borderTop: "1px solid var(--line)", paddingTop: 20 }}>
            <h2>История действий пользователя</h2>
            <p className="muted" style={{ margin: "6px 0 16px" }}>
              Аудит операций пользователя в Cassandra
            </p>
            <HistoryFeed
              key={user.id}
              fetchPage={useCallback(
                (cursor?: string | null) =>
                  getUserHistory(user.id, { limit: 15, last_event_id: cursor }),
                [user.id],
              )}
              showUserId={false}
              emptyText="Событий для данного пользователя нет"
            />
          </div>
        </>
      ) : null}
    </>
  );
}
