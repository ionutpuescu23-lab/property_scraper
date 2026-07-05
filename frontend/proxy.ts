import { type NextRequest, NextResponse } from 'next/server'

export function proxy(request: NextRequest) {
  const expectedPassword = process.env.STAGING_PASSWORD;
  const authCookie = request.cookies.get('staging_auth')?.value;
  const url = request.nextUrl.clone();
  
  // 1. If the secret password is in the URL parameters, set the cookie and unlock the site
  const passParam = url.searchParams.get('pass');
  if (passParam === expectedPassword && expectedPassword) {
    const response = NextResponse.redirect(new URL(url.pathname, request.url));
    response.cookies.set('staging_auth', expectedPassword, { 
      httpOnly: true, 
      maxAge: 60 * 60 * 24 * 7 // Keeps you logged in for 7 days
    });
    return response;
  }

  // 2. If they don't have the valid cookie, show a clean, locked gate screen
  if (expectedPassword && authCookie !== expectedPassword) {
    return new NextResponse(
      `<html>
        <head><title>AlphaDeals Staging</title></head>
        <body style="background:#121212; color:#e2e8f0; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; margin:0;">
          <div style="text-align:center; border: 1px solid #2d3748; padding: 2.5rem; border-radius: 8px; background: #1a202c;">
            <h2 style="margin-top:0; color:#ed8936;">AlphaDeals Staging</h2>
            <p style="color:#a0aec0;">This pipeline staging area is private.</p>
          </div>
        </body>
      </html>`,
      { status: 401, headers: { 'content-type': 'text/html' } }
    );
  }

  return NextResponse.next();
}

export const config = {
  // Protect all routes except Next.js internals and static assets
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};