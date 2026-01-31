import { createFileRoute, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  const { isAuthenticated, user } = useAuth()

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-4 text-center">
      <h1 className="mb-4 font-display text-[clamp(2rem,5vw,3rem)] font-bold leading-tight text-foreground">
        Strictly Dancing
      </h1>
      <p className="mb-8 max-w-xl text-[clamp(1rem,2.5vw,1.25rem)] leading-relaxed text-muted-foreground">
        Connect with qualified dance hosts around the world.
        Whether you're traveling or looking for a dance partner locally,
        we've got you covered.
      </p>

      {isAuthenticated && user ? (
        <div className="flex flex-col items-center gap-4">
          <p className="text-foreground">
            Welcome back, {user.first_name}!
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button asChild size="lg">
              <Link to="/hosts" className="no-underline">
                Find a Host
              </Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap justify-center gap-4">
          <Button asChild size="lg">
            <Link to="/hosts" className="no-underline">
              Find a Host
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link to="/register" className="no-underline">
              Become a Host
            </Link>
          </Button>
        </div>
      )}
    </div>
  )
}
