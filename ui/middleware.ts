import { NextRequest, NextResponse } from 'next/server';

const defaultLocale = 'en';
const locales = ['en', 'zh', 'fr', 'es'];

// Special routes that should be exempted from direct locale prefixing
const authRoutes = ['/login', '/register', '/verify', '/signin', '/signup', '/auth'];
const dashboardRoutes = ['/chat', '/profile', '/settings', '/family', '/sessions'];

// Get the preferred locale, similar to the above or using a different detection strategy
function getLocale(request: NextRequest) {
  // Check if the path includes a locale
  const pathname = request.nextUrl.pathname;
  const pathnameHasLocale = locales.some(
    locale => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (pathnameHasLocale) {
    // Return the detected locale from URL
    return pathname.split('/')[1];
  }

  // Check for locale in cookies or Accept-Language header
  const acceptLanguage = request.headers.get('accept-language') || '';
  const localeFromHeader = acceptLanguage.split(',')[0].split('-')[0];

  if (locales.includes(localeFromHeader)) {
    return localeFromHeader;
  }

  return defaultLocale;
}

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // Always skip processing for static files including locales
  if (
    pathname.startsWith('/locales/') || 
    pathname.includes('.') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/api/')
  ) {
    console.log(`Skipping middleware for static path: ${pathname}`);
    return NextResponse.next();
  }

  // Check if the path is an auth route that should be specially handled
  const isAuthRoute = authRoutes.some(route => pathname === route || pathname.startsWith(`${route}/`));
  if (isAuthRoute) {
    // For auth routes, we don't add the locale prefix, we handle it differently via redirects
    console.log(`Auth route detected: ${pathname}`);
    
    // If it's already a locale prefixed auth route, like /en/login, redirect to /login?lang=en
    if (locales.some(locale => pathname.startsWith(`/${locale}/login`))) {
      const locale = pathname.split('/')[1];
      const url = new URL(`/login?lang=${locale}`, request.url);
      return NextResponse.redirect(url);
    }
    
    return NextResponse.next();
  }
  
  // Similarly handle dashboard routes specially
  const isDashboardRoute = dashboardRoutes.some(route => pathname === route || pathname.startsWith(`${route}/`));
  if (isDashboardRoute) {
    // For dashboard routes, ensure they have a locale prefix
    const locale = getLocale(request);
    
    // If route doesn't already have locale, add it
    const pathnameHasLocale = locales.some(
      locale => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
    );
    
    if (!pathnameHasLocale) {
      // For a path like /chat, redirect to /en/chat
      const url = new URL(`/${locale}${pathname}`, request.url);
      url.search = request.nextUrl.search;
      return NextResponse.redirect(url);
    }
    
    return NextResponse.next();
  }
  
  // Check if the path already has a locale
  const pathnameHasLocale = locales.some(
    locale => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (pathnameHasLocale) {
    // If URL already has locale, just forward the request
    return NextResponse.next();
  }

  // Redirect to the locale version
  const locale = getLocale(request);
  const url = new URL(`/${locale}${pathname === '/' ? '' : pathname}`, request.url);
  url.search = request.nextUrl.search;
  
  return NextResponse.redirect(url);
}

export const config = {
  matcher: [
    // Skip all internal paths (_next, assets, etc)
    '/((?!_next|api|locales|images|favicon.ico).*)',
  ],
}; 