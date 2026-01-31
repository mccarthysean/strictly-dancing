import { createRootRoute, Link, Outlet, useRouter } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import { useAuth } from '@/contexts/AuthContext'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export const Route = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
})

function RootLayout() {
  const { isAuthenticated, user, isLoading } = useAuth()

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <nav className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <Link to="/" className="font-display text-lg font-bold text-rose-600 no-underline dark:text-rose-gold-400">
            Strictly Dancing
          </Link>
          <div className="flex flex-wrap items-center gap-1 sm:gap-2">
            {isLoading ? (
              <span className="px-2 text-muted-foreground">...</span>
            ) : isAuthenticated ? (
              <>
                <Link
                  to="/hosts"
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium text-foreground/80 no-underline transition-colors",
                    "hover:bg-accent hover:text-foreground"
                  )}
                >
                  Find Hosts
                </Link>
                <Link
                  to="/bookings"
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium text-foreground/80 no-underline transition-colors",
                    "hover:bg-accent hover:text-foreground"
                  )}
                >
                  Bookings
                </Link>
                <Link
                  to="/messages"
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium text-foreground/80 no-underline transition-colors",
                    "hover:bg-accent hover:text-foreground"
                  )}
                >
                  Messages
                </Link>
                {(user?.user_type === 'host' || user?.user_type === 'both') && (
                  <Link
                    to="/host/dashboard"
                    className={cn(
                      "rounded-md px-3 py-2 text-sm font-medium text-foreground/80 no-underline transition-colors",
                      "hover:bg-accent hover:text-foreground"
                    )}
                  >
                    Dashboard
                  </Link>
                )}
                <ThemeToggle />
                <Link to="/settings" className="no-underline">
                  <Avatar size="sm" className="cursor-pointer ring-2 ring-rose-600/20 transition-all hover:ring-rose-600/40 dark:ring-rose-gold-400/20 dark:hover:ring-rose-gold-400/40">
                    <AvatarFallback className="bg-rose-600 text-white dark:bg-rose-gold-400 dark:text-foreground">
                      {user?.first_name?.charAt(0) ?? '?'}
                    </AvatarFallback>
                  </Avatar>
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/hosts"
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium text-foreground/80 no-underline transition-colors",
                    "hover:bg-accent hover:text-foreground"
                  )}
                >
                  Browse
                </Link>
                <Link
                  to="/login"
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium text-foreground/80 no-underline transition-colors",
                    "hover:bg-accent hover:text-foreground"
                  )}
                >
                  Login
                </Link>
                <ThemeToggle />
                <Button asChild size="sm">
                  <Link to="/register" className="no-underline">
                    Register
                  </Link>
                </Button>
              </>
            )}
          </div>
        </nav>
      </header>
      <main className="min-h-[calc(100vh-60px)] bg-background">
        <Outlet />
      </main>
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </>
  )
}

function NotFoundComponent() {
  return (
    <div className="flex min-h-[80vh] items-center justify-center p-4">
      <div className="w-full max-w-md text-center">
        <div className="mb-2 text-[clamp(5rem,15vw,8rem)] font-extrabold leading-none text-muted-foreground/20">
          404
        </div>
        <h1 className="mb-3 font-display text-2xl font-bold text-foreground">
          Page Not Found
        </h1>
        <p className="mb-6 leading-relaxed text-muted-foreground">
          Sorry, we couldn't find the page you're looking for.
          It might have been moved or doesn't exist.
        </p>
        <div className="flex flex-col gap-3">
          <Button asChild className="w-full">
            <Link to="/" className="no-underline">
              Go to Home
            </Link>
          </Button>
          <Button asChild variant="outline" className="w-full">
            <Link to="/hosts" className="no-underline">
              Browse Hosts
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

function ErrorComponent() {
  const router = useRouter()
  const matches = router.state.matches
  const lastMatch = matches[matches.length - 1]
  const error = lastMatch?.error as Error | undefined

  return (
    <div className="flex min-h-[80vh] items-center justify-center p-4">
      <div className="w-full max-w-lg rounded-2xl bg-card p-10 text-center shadow-lg">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10">
          <span className="text-4xl text-destructive">&#9888;</span>
        </div>
        <h1 className="mb-3 font-display text-2xl font-bold text-foreground">
          Something went wrong
        </h1>
        <p className="mb-6 leading-relaxed text-muted-foreground">
          We encountered an error while loading this page. Please try again.
        </p>
        {error && (
          <p className="mb-6 rounded-lg bg-destructive/10 px-4 py-3 font-mono text-sm text-destructive">
            {error.message}
          </p>
        )}
        <div className="flex flex-col gap-3">
          <Button
            onClick={() => window.location.reload()}
            className="w-full"
          >
            Refresh Page
          </Button>
          <Button asChild variant="outline" className="w-full">
            <Link to="/" className="no-underline">
              Go to Home
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
