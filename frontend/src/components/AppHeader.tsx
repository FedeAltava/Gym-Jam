import { Link } from 'react-router-dom';

export function AppHeader() {
  return (
    <header
      className="fixed top-0 left-0 right-0 md:left-60 z-20 flex items-center justify-between px-4 bg-surface border-b border-border"
      style={{
        height: '56px',
        paddingTop: 'env(safe-area-inset-top)',
      }}
    >
      <Link
        to="/dashboard"
        className="text-lg font-bold tracking-tight no-underline md:hidden"
      >
        <span className="text-text">Gym</span>
        <span className="text-accent">Jam</span>
      </Link>
      <span className="hidden md:block text-sm font-semibold text-muted">GymJam</span>
    </header>
  );
}
