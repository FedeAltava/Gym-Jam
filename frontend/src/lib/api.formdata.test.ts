/**
 * Tests for apiFetch FormData guard:
 * When body is a FormData instance, Content-Type must NOT be set to
 * 'application/json' so the browser can set the multipart boundary.
 */
import { apiFetch } from './api';

vi.mock('../store/authStore', () => ({
  useAuthStore: {
    getState: () => ({ token: 'test-token', user: { id: 'u1', email: 'e@e.com' } }),
    subscribe: vi.fn(),
  },
}));

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

afterEach(() => {
  vi.clearAllMocks();
});

describe('apiFetch — FormData guard', () => {
  it('does NOT set Content-Type when body is FormData', async () => {
    mockFetch.mockResolvedValue(
      new Response(JSON.stringify({ id: '1' }), { status: 200 }),
    );

    const fd = new FormData();
    fd.append('file', new Blob(['pdf'], { type: 'application/pdf' }), 'test.pdf');

    await apiFetch('/nutrition/menus', { method: 'POST', body: fd });

    const [, fetchOptions] = mockFetch.mock.calls[0] as [string, RequestInit & { headers: Record<string, string> }];
    const contentType = (fetchOptions.headers as Record<string, string>)['Content-Type'];
    expect(contentType).toBeUndefined();
  });

  it('sets Content-Type: application/json when body is NOT FormData', async () => {
    mockFetch.mockResolvedValue(
      new Response(JSON.stringify({ id: '2' }), { status: 200 }),
    );

    await apiFetch('/workouts', { method: 'POST', body: JSON.stringify({ name: 'Test' }) });

    const [, fetchOptions] = mockFetch.mock.calls[0] as [string, RequestInit & { headers: Record<string, string> }];
    const contentType = (fetchOptions.headers as Record<string, string>)['Content-Type'];
    expect(contentType).toBe('application/json');
  });
});
