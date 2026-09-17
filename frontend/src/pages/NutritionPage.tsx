import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNutritionMenus, useNutritionMenu } from '../hooks/useNutrition';
import { Spinner } from '../components/Spinner';
import { UploadMenuForm } from '../components/nutrition/UploadMenuForm';
import { WeeklyMenuView } from '../components/nutrition/WeeklyMenuView';
import type { ParsedMenu } from '../types/api';

type PageView = 'list' | 'upload' | 'menu';

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function MenuDetailView({ id, onBack }: { id: string; onBack: () => void }) {
  const { data: plan, isLoading } = useNutritionMenu(id);

  let parsedMenu: ParsedMenu | null = null;
  if (plan?.menu_json) {
    try {
      parsedMenu = JSON.parse(plan.menu_json) as ParsedMenu;
    } catch {
      // malformed JSON — treat as null
    }
  }

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
          <h2
            style={{
              fontSize: '22px',
              fontWeight: 700,
              color: 'var(--text)',
              marginBottom: '16px',
              fontFamily: "'Barlow Semi Condensed', sans-serif",
            }}
          >
            {plan?.title}
          </h2>
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

  const handleMenuCardClick = (id: string) => {
    setSelectedMenuId(id);
    setView('menu');
  };

  const handleUploadSuccess = () => {
    setView('list');
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

        {isLoading ? (
          <Spinner />
        ) : menus && menus.length > 0 ? (
          <div>
            {menus.map((menu) => (
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
          <button
            type="button"
            onClick={() => setView('upload')}
            style={{
              width: '100%',
              height: '54px',
              border: 'none',
              borderRadius: '18px',
              background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
              color: 'rgb(6,33,15)',
              fontSize: '16px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Subir menú
          </button>
        </div>
      </div>
    );
  }

  // ── Upload view ──────────────────────────────────────────────────────────
  if (view === 'upload') {
    return (
      <div>
        <button
          type="button"
          onClick={() => setView('list')}
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
        <UploadMenuForm onSuccess={handleUploadSuccess} />
      </div>
    );
  }

  // ── Menu detail view ─────────────────────────────────────────────────────
  return (
    <MenuDetailView id={selectedMenuId} onBack={() => setView('list')} />
  );
}
