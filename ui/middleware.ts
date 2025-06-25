import { NextRequest, NextResponse } from 'next/server';

const defaultLocale = 'en';
const locales = ['en', 'zh', 'fr', 'es'];

// Special routes that should be exempted from direct locale prefixing
const authRoutes = ['/login', '/register', '/verify', '/signin', '/signup', '/auth'];
const dashboardRoutes = ['/chat', '/profile', '/settings', '/family', '/sessions'];

// Get the preferred locale
function getLocale(request: NextRequest) {
  // Check if the path includes a locale
  const pathname = request.nextUrl.pathname;
  const pathnameHasLocale = locales.some(
    locale => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (pathnameHasLocale) {
    return pathname.split('/')[1];
  }

  // Check for locale in cookies
  const cookieLocale = request.cookies.get('NEXT_LOCALE')?.value;
  if (cookieLocale && locales.includes(cookieLocale)) {
    return cookieLocale;
  }

  // Check Accept-Language header
  const acceptLanguage = request.headers.get('accept-language') || '';
  const localeFromHeader = acceptLanguage.split(',')[0].split('-')[0];

  if (locales.includes(localeFromHeader)) {
    return localeFromHeader;
  }

  return defaultLocale;
}

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // Skip processing for static files and API routes
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/api/') ||
    pathname.startsWith('/static/') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Handle auth routes
  const isAuthRoute = authRoutes.some(route => pathname === route || pathname.startsWith(`${route}/`));
  if (isAuthRoute) {
    // For auth routes, preserve the original path but add locale as a query parameter
    const locale = getLocale(request);
    const url = new URL(pathname, request.url);
    url.searchParams.set('lang', locale);
    return NextResponse.rewrite(url);
  }

  // Handle dashboard routes
  const isDashboardRoute = dashboardRoutes.some(route => pathname === route || pathname.startsWith(`${route}/`));
  if (isDashboardRoute) {
    const locale = getLocale(request);
    
    // If route doesn't have locale, add it
    const pathnameHasLocale = locales.some(
      locale => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
    );
    
    if (!pathnameHasLocale) {
      const url = new URL(`/${locale}${pathname}`, request.url);
      url.search = request.nextUrl.search;
      return NextResponse.redirect(url);
    }
    
    return NextResponse.next();
  }

  // Handle root path
  if (pathname === '/') {
    const locale = getLocale(request);
    return NextResponse.redirect(new URL(`/${locale}`, request.url));
  }

  // For all other routes, ensure they have a locale prefix
  const pathnameHasLocale = locales.some(
    locale => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (!pathnameHasLocale) {
    const locale = getLocale(request);
    const url = new URL(`/${locale}${pathname}`, request.url);
    url.search = request.nextUrl.search;
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Skip all internal paths (_next, api, etc)
    '/((?!_next|api|static|favicon.ico).*)',
  ],
}; 