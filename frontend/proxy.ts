import { type NextRequest, NextResponse } from 'next/server'

export function proxy(request: NextRequest) {
  // Hardcode a reliable temporary password here if the Vercel key fails to pass through
  const expectedPassword = process.env.STAGING_PASSWORD || 'liverpool-deals-2026';
  
  const authCookie = request.cookies.get('staging_auth')?.value;
  const url = request.nextUrl.clone();
  
  // 1. URL checker (?pass=...)
  const passParam = url.searchParams.get('pass');
  if (passParam === expectedPassword) {
    const response = NextResponse.redirect(new URL(url.pathname, request.url));
    response.cookies.set('staging_auth', expectedPassword, { 
      httpOnly: true, 
      maxAge: 60 * 60 * 24 * 7, 
      path: '/'
    });
    return response;
  }

  // 2. Clear passage if cookie matches perfectly
  if (authCookie === expectedPassword) {
    return NextResponse.next();
  }

  // 3. Absolute block if no match found
  return new NextResponse(
    `<html>
      <head>
        <title>AlphaDeals Staging</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="background:#121212; color:#e2e8f0; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; margin:0;">
        <div style="text-align:center; border: 1px solid #2d3748; padding: 2.5rem; border-radius: 8px; background: #1a202c; max-width: 400px; margin: 20px;">
          <h2 style="margin-top:0; color:#ed8936; font-size: 24px;">AlphaDeals Staging</h2>
          <p style="color:#a0aec0; line-height: 1.5;">This pipeline staging area is private while configuration is finalized.</p>
        </div>
      </body>
    </html>`,
    { 
      status: 401, 
      headers: { 'content-type': 'text/html; charset=utf-8' } 
    }
  );
}

export const config = {
  // Catch everything except static assets
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};