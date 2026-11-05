import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { changePassword, deleteAccount, logoutAll, updateProfile } from "../api/auth";
import { ApiError } from "../api/client";
import { getMyHistory } from "../api/history";
import { useAuth } from "../auth/AuthContext";
import { HistoryFeed } from "../components/HistoryFeed";
import { roleLabel } from "../lib/format";

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, setUser, logout } = useAuth();
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function onSaveProfile(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const next = await updateProfile(name, email);
      setUser(next);
      setMessage("Профиль сохранён");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сохранить профиль");
    }
  }

  async function onChangePassword(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await changePassword(oldPassword, newPassword);
      setOldPassword("");
      setNewPassword("");
      setMessage("Пароль изменён");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сменить пароль");
    }
  }

  async function onLogoutAll() {
    try {
      await logoutAll();
      await logout();
      navigate("/login", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось выйти везде");
    }
  }

  async function onDelete() {
    if (!window.confirm("Удалить аккаунт безвозвратно?")) return;
    try {
      await deleteAccount();
      await logout();
      navigate("/register", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось удалить аккаунт");
    }
  }

  return (
    <div className="card profile">
      <h1>Профиль</h1>
      <p className="muted" style={{ margin: "8px 0 20px" }}>
        Роль: {roleLabel(user?.role ?? "STUDENT")} · {user?.id}
      </p>
      {error ? <p className="error">{error}</p> : null}
      {message ? <p className="ok">{message}</p> : null}
      <form onSubmit={onSaveProfile}>
        <label className="field">
          <span>Имя</span>
          <input value={name} minLength={2} onChange={(event) => setName(event.target.value)} />
        </label>
        <label className="field">
          <span>Email</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <button className="btn btn--primary" type="submit">
          Сохранить
        </button>
      </form>
      <form onSubmit={onChangePassword} style={{ marginTop: 28 }}>
        <h2>Смена пароля</h2>
        <label className="field" style={{ marginTop: 12 }}>
          <span>Текущий пароль</span>
          <input
            type="password"
            value={oldPassword}
            onChange={(event) => setOldPassword(event.target.value)}
          />
        </label>
        <label className="field">
          <span>Новый пароль</span>
          <input
            type="password"
            minLength={6}
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
        </label>
        <button className="btn btn--ghost" type="submit">
          Сменить пароль
        </button>
      </form>
      <div className="row__actions" style={{ marginTop: 28 }}>
        <button type="button" className="btn btn--ghost" onClick={() => void onLogoutAll()}>
          Выйти на всех устройствах
        </button>
        <button type="button" className="btn btn--danger" onClick={() => void onDelete()}>
          Удалить аккаунт
        </button>
      </div>

      <div style={{ marginTop: 36, borderTop: "1px solid var(--line)", paddingTop: 24 }}>
        <h2>История действий</h2>
        <p className="muted" style={{ margin: "6px 0 16px" }}>
          Журнал операций вашего аккаунта (сохраняется в Apache Cassandra)
        </p>
        <HistoryFeed
          fetchPage={(cursor) =>
            getMyHistory({ limit: 10, last_event_id: cursor })
          }
          showUserId={false}
          emptyText="У вас пока нет зарегистрированных действий"
        />
      </div>
    </div>
  );
}
