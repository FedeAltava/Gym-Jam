import { useState, useRef, useEffect } from 'react';
import type { DietPlan } from '../../types/api';
import { useUploadNutritionMenu } from '../../hooks/useNutrition';
import { Spinner } from '../Spinner';

interface UploadMenuFormProps {
  onSuccess: (dietPlan: DietPlan) => void;
}

type UploadState = 'idle' | 'picked' | 'processing' | 'done';

export function UploadMenuForm({ onSuccess }: UploadMenuFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [pickedFile, setPickedFile] = useState<File | null>(null);
  const [uiState, setUiState] = useState<UploadState>('idle');
  const mutation = useUploadNutritionMenu();

  useEffect(() => {
    if (uiState !== 'processing') return;
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
  }, [uiState]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPickedFile(file);
      setUiState('picked');
    }
  };

  const handleProcess = () => {
    if (!pickedFile) return;
    const fd = new FormData();
    fd.append('file', pickedFile);
    setUiState('processing');
    mutation.mutate(fd, {
      onSuccess: (data) => {
        setUiState('done');
        onSuccess(data);
      },
      onError: () => {
        setUiState('picked');
      },
    });
  };

  const handleViewMenu = () => {
    if (mutation.data) onSuccess(mutation.data);
  };

  // ── Idle ─────────────────────────────────────────────────────────────────
  if (uiState === 'idle') {
    return (
      <div
        style={{
          border: '2px dashed rgba(43,229,129,0.35)',
          borderRadius: '20px',
          padding: '40px 24px',
          textAlign: 'center',
        }}
      >
        <p
          style={{
            fontSize: '17px',
            fontWeight: 700,
            color: 'var(--text)',
            marginBottom: '8px',
          }}
        >
          Sube el PDF de tu nutricionista
        </p>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#8B928A',
            fontSize: '14px',
            cursor: 'pointer',
          }}
        >
          Toca para elegir un archivo
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </div>
    );
  }

  // ── Picked ───────────────────────────────────────────────────────────────
  if (uiState === 'picked') {
    return (
      <div
        style={{
          background: '#14160F',
          border: '1px solid #22251E',
          borderRadius: '16px',
          padding: '24px',
          textAlign: 'center',
        }}
      >
        <p
          style={{ color: 'var(--text)', fontSize: '15px', marginBottom: '16px' }}
        >
          {pickedFile?.name}
        </p>
        <button
          type="button"
          onClick={handleProcess}
          style={{
            height: '48px',
            padding: '0 28px',
            background: '#2BE581',
            color: '#090B09',
            border: 'none',
            borderRadius: '14px',
            fontSize: '16px',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          Procesar PDF
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </div>
    );
  }

  // ── Processing ───────────────────────────────────────────────────────────
  if (uiState === 'processing') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px',
          padding: '40px 24px',
        }}
      >
        <Spinner />
        <p style={{ color: '#8B928A', fontSize: '15px' }}>Leyendo tu PDF...</p>
      </div>
    );
  }

  // ── Done ─────────────────────────────────────────────────────────────────
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px',
        padding: '40px 24px',
        textAlign: 'center',
      }}
    >
      {/* Green checkmark circle */}
      <div
        style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: 'rgba(43,229,129,0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span style={{ fontSize: '32px' }}>✓</span>
      </div>
      <p
        style={{ color: 'var(--text)', fontSize: '17px', fontWeight: 700 }}
      >
        Tu menú semanal está listo
      </p>
      <button
        type="button"
        onClick={handleViewMenu}
        style={{
          height: '48px',
          padding: '0 28px',
          background: '#2BE581',
          color: '#090B09',
          border: 'none',
          borderRadius: '14px',
          fontSize: '16px',
          fontWeight: 700,
          cursor: 'pointer',
        }}
      >
        Ver menú
      </button>
    </div>
  );
}
