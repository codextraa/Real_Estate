// src/app/api/auth-secret-key/route.js
export async function GET() {
  const authSecretKey = process.env.NEXT_PUBLIC_AUTH_SECRET_KEY;
  return new Response(JSON.stringify({ authSecretKey }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
