import { renderHook, act } from '@testing-library/react';
import { useScreenWakeLock } from './useScreenWakeLock';

describe('useScreenWakeLock', () => {
  const release = vi.fn();
  const request = vi.fn();

  beforeEach(() => {
    release.mockReset().mockResolvedValue(undefined);
    request.mockReset().mockResolvedValue({ release });
    Object.defineProperty(navigator, 'wakeLock', {
      value: { request },
      configurable: true,
    });
  });

  afterEach(() => {
    delete (navigator as { wakeLock?: unknown }).wakeLock;
  });

  it('does not request a lock while inactive', () => {
    renderHook(() => useScreenWakeLock(false));
    expect(request).not.toHaveBeenCalled();
  });

  it('requests a screen lock while active and releases it when deactivated', async () => {
    const { rerender } = renderHook(({ active }) => useScreenWakeLock(active), {
      initialProps: { active: true },
    });
    await act(async () => {});
    expect(request).toHaveBeenCalledWith('screen');

    rerender({ active: false });
    expect(release).toHaveBeenCalled();
  });

  it('re-acquires the lock when the page becomes visible again', async () => {
    renderHook(() => useScreenWakeLock(true));
    await act(async () => {});
    expect(request).toHaveBeenCalledTimes(1);

    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(request).toHaveBeenCalledTimes(2);
  });
});
