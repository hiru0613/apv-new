const T = "http://115.159.157.79:8787";

async function go(req: Request) {
  const u = new URL(req.url);
  const p = u.pathname.replace("/api/hub-proxy", "") || "/";
  const h: Record<string, string> = { "content-type": "application/json" };
  const a = req.headers.get("authorization");
  if (a) h["authorization"] = a;
  const r = await fetch(T + p + u.search, {
    method: req.method,
    headers: h,
    body: req.method === "GET" ? undefined : await req.text(),
  });
  return new Response(await r.text(), {
    status: r.status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

export async function POST(req: Request) { return go(req); }
export async function GET(req: Request) { return go(req); }
export const dynamic = "force-dynamic";
