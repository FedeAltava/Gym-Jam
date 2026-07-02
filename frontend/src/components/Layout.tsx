import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { BottomNav } from './BottomNav';
import { AppHeader } from './AppHeader';

export function Layout() {
  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <div className="md:pl-60 flex flex-col min-h-screen">
        <AppHeader />
        <main
          className="flex-1 px-4 md:px-8 w-full max-w-[1200px] mx-auto"
          style={{
            paddingTop: 'calc(56px + 16px)',
            paddingBottom: 'calc(80px + env(safe-area-inset-bottom))',
          }}
        >
          <Outlet />
        </main>
      </div>
      <BottomNav />
    </div>
  );
}
