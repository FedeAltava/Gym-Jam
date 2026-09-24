import { useEffect } from 'react';

/**
 * Keeps the screen awake while `active` is true (e.g. during a long PDF
 * upload). Re-acquires the lock when the page becomes visible again, since
 * browsers release it automatically when the tab is hidden.
 */
export function useScreenWakeLock(active: boolean) {
  useEffect(() => {
    if (!active) return;
    if (!('wakeLock' in navigator)) return;

    let lock: WakeLockSentinel | null = null;

    async function acquire() {
      try {
        lock = await navigator.wakeLock.request('screen');
      } catch {
        // Permission denied or feature unavailable — no action needed.
      }
    }

    function handleVisibilityChange() {
      if (document.visibilityState === 'visible') acquire();
    }

    acquire();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      lock?.release();
    };
  }, [active]);
}
