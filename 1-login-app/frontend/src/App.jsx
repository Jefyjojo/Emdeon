import { useState, useEffect } from "react";

const API = "http://localhost:8000";

export default function App() {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [user, setUser] = useState(null);

  // Restore session if a token exists
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    fetch(`${API}/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setUser)
      .catch(() => localStorage.removeItem("token"));
  }, []);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");
    const body =
      mode === "register"
        ? form
        : { email: form.email, password: form.password };
    try {
      const res = await fetch(`${API}/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Something went wrong");

      if (mode === "register") {
        setSuccess("Registered! You can log in now.");
        setMode("login");
      } else {
        localStorage.setItem("token", data.token);
        setUser({ name: data.name, email: form.email });
      }
    } catch (err) {
      setError(err.message);
    }
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
    setForm({ name: "", email: "", password: "" });
  }

  if (user) {
    return (
      <div className="card">
        <h2>Welcome, {user.name}</h2>
        <p>{user.email}</p>
        <button onClick={logout}>Log out</button>
      </div>
    );
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>{mode === "login" ? "Login" : "Register"}</h2>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      {mode === "register" && (
        <input name="name" placeholder="Name" value={form.name} onChange={onChange} required />
      )}
      <input name="email" type="email" placeholder="Email" value={form.email} onChange={onChange} required />
      <input name="password" type="password" placeholder="Password" value={form.password} onChange={onChange} required />
      <button type="submit">{mode === "login" ? "Login" : "Create account"}</button>
      <button
        type="button"
        className="link"
        onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
      >
        {mode === "login" ? "No account? Register" : "Have an account? Login"}
      </button>
    </form>
  );
}
