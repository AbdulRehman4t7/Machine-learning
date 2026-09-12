import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse
import webbrowser

import requests


HOST = "127.0.0.1"
PORT = 8000


def github_profile(username):
    """Return the public GitHub profile for a username."""
    username = username.strip()
    if not username or len(username) > 39:
        raise ValueError("Enter a valid GitHub username.")

    response = requests.get(
        f"https://api.github.com/users/{quote(username)}",
        headers={
            "Accept": "application/vnd.github+json",
            **(
                {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
                if os.environ.get("GITHUB_TOKEN")
                else {}
            ),
        },
        timeout=10,
    )

    if response.status_code == 404:
        raise LookupError("We couldn't find a GitHub user with that username.")
    if response.status_code == 403:
        raise PermissionError(
            "GitHub API rate limit reached. Set a GITHUB_TOKEN and restart the app."
        )
    response.raise_for_status()
    return response.json()


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitHub Profile Explorer</title>
  <style>
    :root { color-scheme: dark; --ink:#f6f7fb; --muted:#aab4cc; --accent:#8b5cf6; }
    * { box-sizing:border-box; }
    body {
      margin:0; min-height:100vh; color:var(--ink);
      font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background:radial-gradient(circle at 10% 0%, #26366b 0, #13172b 38%, #090b16 100%);
    }
    .shell { width:min(1040px, calc(100% - 32px)); margin:auto; padding:64px 0; }
    .hero { text-align:center; margin-bottom:34px; }
    .eyebrow { color:#c4b5fd; letter-spacing:.16em; text-transform:uppercase; font-size:.75rem; font-weight:800; }
    h1 { margin:13px 0 10px; font-size:clamp(2.3rem,6vw,4.8rem); line-height:1; }
    .hero p { color:var(--muted); font-size:1.08rem; margin:0; }
    .search { display:flex; gap:10px; max-width:680px; margin:30px auto 0; padding:8px; border:1px solid #ffffff20; background:#ffffff0d; border-radius:18px; backdrop-filter:blur(18px); }
    input { flex:1; min-width:0; border:0; outline:0; color:var(--ink); background:transparent; padding:14px 16px; font-size:1rem; }
    button { border:0; border-radius:12px; padding:0 25px; color:white; background:linear-gradient(135deg,#7c3aed,#2563eb); font-weight:800; cursor:pointer; transition:transform .2s,opacity .2s; }
    button:hover { transform:translateY(-2px); } button:disabled { opacity:.6; cursor:wait; transform:none; }
    #message { min-height:28px; margin:18px 0; text-align:center; color:#fca5a5; }
    .card { display:none; overflow:hidden; border:1px solid #ffffff1c; border-radius:28px; background:#ffffff0d; box-shadow:0 24px 80px #0005; backdrop-filter:blur(20px); }
    .card.show { display:block; animation:rise .35s ease-out; }
    .profile { display:flex; align-items:center; gap:22px; padding:30px; background:linear-gradient(115deg,#ffffff12,#ffffff03); }
    .avatar { width:112px; height:112px; border-radius:50%; border:4px solid #ffffff35; box-shadow:0 8px 30px #0006; }
    h2 { margin:0 0 5px; font-size:1.9rem; } .login { color:#c4b5fd; font-size:1rem; }
    .bio { color:var(--muted); margin:13px 0 0; max-width:650px; line-height:1.5; }
    .visit { margin-left:auto; padding:11px 16px; border-radius:10px; color:white; text-decoration:none; background:#ffffff18; font-weight:700; white-space:nowrap; }
    .stats { display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:#ffffff16; }
    .stat { padding:24px; text-align:center; background:#101326; } .stat strong { display:block; font-size:1.7rem; } .stat span { color:var(--muted); font-size:.85rem; }
    .details { display:flex; flex-wrap:wrap; gap:12px 26px; padding:22px 30px; color:var(--muted); font-size:.92rem; }
    @keyframes rise { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
    @media (max-width:620px) { .shell { padding:38px 0; } .profile { flex-direction:column; text-align:center; } .visit { margin:0; } .search { flex-direction:column; } button { padding:14px; } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">GitHub profile explorer</div>
      <h1>Discover developers.</h1>
      <p>Search any public GitHub profile and see their community at a glance.</p>
      <form class="search" id="searchForm">
        <input id="username" name="username" placeholder="Try torvalds or octocat" autocomplete="off" required>
        <button id="searchButton" type="submit">Search profile</button>
      </form>
    </section>
    <div id="message"></div>
    <article class="card" id="profileCard">
      <div class="profile">
        <img class="avatar" id="avatar" alt="">
        <div>
          <h2 id="name"></h2><div class="login" id="login"></div>
          <p class="bio" id="bio"></p>
        </div>
        <a class="visit" id="link" target="_blank" rel="noreferrer">View on GitHub ↗</a>
      </div>
      <div class="stats">
        <div class="stat"><strong id="repos"></strong><span>Repositories</span></div>
        <div class="stat"><strong id="followers"></strong><span>Followers</span></div>
        <div class="stat"><strong id="following"></strong><span>Following</span></div>
      </div>
      <div class="details"><span id="location"></span><span id="company"></span><span id="joined"></span></div>
    </article>
  </main>
  <script>
    const form = document.querySelector("#searchForm");
    const input = document.querySelector("#username");
    const button = document.querySelector("#searchButton");
    const message = document.querySelector("#message");
    const card = document.querySelector("#profileCard");
    const text = (id, value) => document.querySelector(id).textContent = value || "Not specified";
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const username = input.value.trim();
      if (!username) return;
      button.disabled = true; message.textContent = "Looking up profile…"; card.classList.remove("show");
      try {
        let response;
        try {
          response = await fetch(`/api/profile?username=${encodeURIComponent(username)}`);
        } catch (networkError) {
          // This also makes the page usable if it was opened directly as a file.
          response = await fetch(`https://api.github.com/users/${encodeURIComponent(username)}`, {
            headers: { "Accept": "application/vnd.github+json" }
          });
        }
        const result = await response.json();
        if (response.status === 404) throw new Error("GitHub user not found.");
        if (!response.ok) throw new Error(result.error || "Something went wrong.");
        document.querySelector("#avatar").src = result.avatar_url;
        document.querySelector("#avatar").alt = `${result.login}'s avatar`;
        text("#name", result.name || result.login); text("#login", `@${result.login}`);
        text("#bio", result.bio); text("#repos", result.public_repos);
        text("#followers", result.followers); text("#following", result.following);
        text("#location", result.location ? `📍 ${result.location}` : "");
        text("#company", result.company ? `🏢 ${result.company}` : "");
        text("#joined", result.created_at ? `Joined ${new Date(result.created_at).toLocaleDateString()}` : "");
        document.querySelector("#link").href = result.html_url;
        message.textContent = ""; card.classList.add("show");
      } catch (error) {
        message.textContent = error.message === "Failed to fetch"
          ? "Unable to connect. Start the Python server and open http://127.0.0.1:8000"
          : error.message;
      }
      finally { button.disabled = false; }
    });
  </script>
</body>
</html>"""


class ProfileHandler(BaseHTTPRequestHandler):
    def send_content(self, body, content_type="text/html; charset=utf-8", status=200):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_content(PAGE)
            return
        if parsed.path == "/api/profile":
            username = parse_qs(parsed.query).get("username", [""])[0]
            try:
                profile = github_profile(username)
                self.send_content(json.dumps(profile), "application/json")
            except (ValueError, LookupError, PermissionError) as error:
                self.send_content(json.dumps({"error": str(error)}), "application/json", 400)
            except requests.RequestException:
                self.send_content(
                    json.dumps({"error": "GitHub is unavailable right now. Please try again."}),
                    "application/json",
                    502,
                )
            return
        self.send_content("Not found", "text/plain; charset=utf-8", 404)

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), ProfileHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"GitHub Profile Explorer running at {url}", flush=True)
    webbrowser.open(url)
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
