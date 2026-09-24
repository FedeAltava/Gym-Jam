import { useRef, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNutritionMenus, useNutritionMenu, useUploadNutritionMenu } from '../hooks/useNutrition';
import { useScreenWakeLock } from '../hooks/useScreenWakeLock';
import { Spinner } from '../components/Spinner';
import { WeeklyMenuView } from '../components/nutrition/WeeklyMenuView';
import { DeleteMenuButton } from '../components/nutrition/DeleteMenuButton';
import { MenuCardSkeleton } from '../components/nutrition/MenuCardSkeleton';
import type { ParsedMenu } from '../types/api';

type PageView = 'list' | 'menu';

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function MenuDetailView({
  id,
  onBack,
  onDeleted,
}: {
  id: string;
  onBack: () => void;
  onDeleted: () => void;
}) {
  const { data: plan, isLoading } = useNutritionMenu(id);

  const parsedMenu: ParsedMenu | null = plan?.menu_json ?? null;

  return (
    <div>
      <button
        type="button"
        onClick={onBack}
        style={{
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--text)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginBottom: '16px',
          fontSize: '15px',
          fontWeight: 600,
          padding: 0,
        }}
      >
        <ArrowLeft size={18} />
        Volver
      </button>

      {isLoading ? (
        <Spinner />
      ) : parsedMenu ? (
        <>
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              gap: '12px',
              marginBottom: '16px',
            }}
          >
            <h2
              style={{
                fontSize: '22px',
                fontWeight: 700,
                color: 'var(--text)',
                margin: 0,
                fontFamily: "'Barlow Semi Condensed', sans-serif",
              }}
            >
              {plan?.title}
            </h2>
            <DeleteMenuButton menuId={id} menuTitle={plan?.title ?? ''} onDeleted={onDeleted} />
          </div>
          <WeeklyMenuView menu={parsedMenu} />
        </>
      ) : (
        <p style={{ color: '#8B928A' }}>No se pudo cargar el menú.</p>
      )}
    </div>
  );
}

export function NutritionPage() {
  const [view, setView] = useState<PageView>('list');
  const [selectedMenuId, setSelectedMenuId] = useState<string>('');
  const { data: menus, isLoading } = useNutritionMenus();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadNutritionMenu();

  // Keep the screen awake while the PDF is being processed.
  useScreenWakeLock(uploadMutation.isPending);

  const handleMenuCardClick = (id: string) => {
    setSelectedMenuId(id);
    setView('menu');
  };

  // After deleting the shown menu, fall back to the list: it refetches and
  // renders the remaining menus or the empty/upload state.
  const handleMenuDeleted = () => {
    setSelectedMenuId('');
    setView('list');
  };

  // Upload starts as soon as a file is picked; the list refetches on success.
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    // Reset so picking the same file again still fires a change event.
    e.target.value = '';
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    uploadMutation.mutate(fd);
  };

  // ── List view ────────────────────────────────────────────────────────────
  if (view === 'list') {
    return (
      <div style={{ paddingBottom: '80px' }}>
        {/* Header */}
        <div style={{ marginBottom: '20px' }}>
          <div
            style={{
              fontSize: '27px',
              fontWeight: 700,
              color: 'var(--text)',
              fontFamily: "'Barlow Semi Condensed', sans-serif",
            }}
          >
            Nutrición
          </div>
          <div style={{ fontSize: '14px', color: '#7E8A7E', fontWeight: 500 }}>
            Tus menús subidos
          </div>
        </div>

        {uploadMutation.isError && (
          <p className="mb-3 text-sm text-danger">No se pudo leer el PDF. Inténtalo de nuevo.</p>
        )}

        {isLoading ? (
          <Spinner />
        ) : uploadMutation.isPending || (menus && menus.length > 0) ? (
          <div>
            {uploadMutation.isPending && <MenuCardSkeleton />}
            {menus?.map((menu) => (
              <article
                key={menu.id}
                onClick={() => handleMenuCardClick(menu.id)}
                style={{
                  background: '#14160F',
                  border: '1px solid #22251E',
                  borderRadius: '16px',
                  padding: '18px 20px',
                  marginBottom: '12px',
                  cursor: 'pointer',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    gap: '12px',
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <h3
                      style={{
                        fontSize: '17px',
                        fontWeight: 700,
                        color: 'var(--text)',
                        margin: '0 0 6px',
                      }}
                    >
                      {menu.title}
                    </h3>
                    <p style={{ fontSize: '13px', color: '#8B928A', margin: 0 }}>
                      {formatDate(menu.uploaded_at)}
                    </p>
                  </div>
                  <DeleteMenuButton menuId={menu.id} menuTitle={menu.title} />
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div
            style={{
              borderRadius: '18px',
              border: '1.5px dashed rgba(43,229,129,0.35)',
              background: 'transparent',
              padding: '32px',
              textAlign: 'center',
            }}
          >
            <p
              style={{
                fontSize: '15px',
                fontWeight: 600,
                color: 'var(--text)',
                marginBottom: '4px',
              }}
            >
              Sin menús todavía
            </p>
            <p
              style={{
                fontSize: '13px',
                color: '#8B928A',
                marginBottom: '0',
              }}
            >
              Sube el PDF de tu nutricionista para verlo aquí
            </p>
          </div>
        )}

        {/* Fixed bottom CTA */}
        <div
          style={{
            position: 'fixed',
            bottom: '72px',
            left: 0,
            right: 0,
            padding: '0 16px',
            zIndex: 20,
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            aria-label="Archivo PDF del menú"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadMutation.isPending}
            className="disabled:opacity-60"
            style={{
              width: '100%',
              height: '54px',
              border: 'none',
              borderRadius: '18px',
              background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
              color: 'rgb(6,33,15)',
              fontSize: '16px',
              fontWeight: 700,
              cursor: uploadMutation.isPending ? 'default' : 'pointer',
            }}
          >
            {uploadMutation.isPending ? 'Leyendo PDF...' : 'Subir menú'}
          </button>
        </div>
      </div>
    );
  }

  // ── Menu detail view ─────────────────────────────────────────────────────
  return (
    <MenuDetailView
      id={selectedMenuId}
      onBack={() => setView('list')}
      onDeleted={handleMenuDeleted}
    />
  );
}
