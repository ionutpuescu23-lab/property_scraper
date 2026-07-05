import staging from 'staging-next';

export const middleware = staging({
  password: process.env.STAGING_PASSWORD, 
});

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};