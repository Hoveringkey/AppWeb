import React, { useEffect, useMemo, useState } from 'react';
import { MagnifyingGlass, FloppyDisk, Trash } from '@phosphor-icons/react';
import api from '../../api/axios';
import { Button, GlassCard, ErrorState } from '../ui';

const PROFILE_TYPES: Array<{ value: string; label: string }> = [
  { value: 'ROTATION_A', label: 'Rotación A (lun-mié / mar-jue)' },
  { value: 'ROTATION_B', label: 'Rotación B (mar-jue / lun-mié)' },
  { value: 'SATURDAY_MONDAY_8H', label: 'Sábado y Lunes 8h' },
  { value: 'FIXED_4DAY', label: 'Fijo Lunes a Jueves' },
  { value: 'FIXED_CUSTOM', label: 'Personalizado' },
];

const WEEKDAY_LABELS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

interface Employee {
  no_nomina: string;
  nombre: string;
}

interface OvertimeProfile {
  id: number;
  empleado: string;
  empleado_nombre?: string;
  profile_type: string;
  custom_weekdays: number[];
  custom_daily_hours: string | null;
  is_active: boolean;
}

interface DraftState {
  empleado: string;
  empleado_nombre: string;
  profile_type: string;
  custom_weekdays: number[];
  custom_daily_hours: string;
  is_active: boolean;
}

const emptyDraft = (): DraftState => ({
  empleado: '',
  empleado_nombre: '',
  profile_type: 'ROTATION_A',
  custom_weekdays: [],
  custom_daily_hours: '',
  is_active: true,
});

const OvertimeProfileManager: React.FC<{ canEdit: boolean }> = ({ canEdit }) => {
  const [profiles, setProfiles] = useState<OvertimeProfile[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [draft, setDraft] = useState<DraftState>(emptyDraft());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profRes, empRes] = await Promise.all([
        api.get('/api/payroll/overtime/profiles/'),
        api.get('/api/payroll/employees/'),
      ]);
      setProfiles(profRes.data ?? []);
      setEmployees(empRes.data ?? []);
    } catch {
      setError('No se pudieron cargar los perfiles.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchAll();
  }, []);

  const employeesById = useMemo(() => {
    const m: Record<string, string> = {};
    employees.forEach(e => { m[e.no_nomina] = e.nombre; });
    return m;
  }, [employees]);

  const filteredProfiles = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return profiles;
    return profiles.filter(p =>
      p.empleado.toLowerCase().includes(q) ||
      (employeesById[p.empleado] ?? '').toLowerCase().includes(q)
    );
  }, [profiles, search, employeesById]);

  const employeeOptions = useMemo(() => {
    const assigned = new Set(profiles.map(p => p.empleado));
    if (editingId !== null) {
      const current = profiles.find(p => p.id === editingId);
      if (current) assigned.delete(current.empleado);
    }
    return employees.filter(e => !assigned.has(e.no_nomina));
  }, [employees, profiles, editingId]);

  const toggleWeekday = (idx: number) => {
    setDraft(prev => {
      const next = new Set(prev.custom_weekdays);
      if (next.has(idx)) next.delete(idx); else next.add(idx);
      return { ...prev, custom_weekdays: Array.from(next).sort((a, b) => a - b) };
    });
  };

  const startEdit = (p: OvertimeProfile) => {
    setEditingId(p.id);
    setDraft({
      empleado: p.empleado,
      empleado_nombre: p.empleado_nombre ?? employeesById[p.empleado] ?? '',
      profile_type: p.profile_type,
      custom_weekdays: p.custom_weekdays ?? [],
      custom_daily_hours: p.custom_daily_hours ?? '',
      is_active: p.is_active,
    });
  };

  const resetForm = () => {
    setEditingId(null);
    setDraft(emptyDraft());
  };

  const save = async () => {
    if (!draft.empleado) {
      setError('Selecciona un empleado.');
      return;
    }
    setSaving(true);
    setError(null);
    const payload: Record<string, unknown> = {
      empleado: draft.empleado,
      profile_type: draft.profile_type,
      is_active: draft.is_active,
      custom_weekdays: draft.profile_type === 'FIXED_CUSTOM' ? draft.custom_weekdays : [],
      custom_daily_hours:
        draft.profile_type === 'FIXED_CUSTOM'
          ? (draft.custom_daily_hours || '0')
          : null,
    };
    try {
      if (editingId !== null) {
        await api.patch(`/api/payroll/overtime/profiles/${editingId}/`, payload);
      } else {
        await api.post('/api/payroll/overtime/profiles/', payload);
      }
      await fetchAll();
      resetForm();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: Record<string, unknown> } };
      const detail = ax.response?.data;
      setError(
        detail
          ? `Error al guardar: ${JSON.stringify(detail)}`
          : 'Error al guardar el perfil.'
      );
    } finally {
      setSaving(false);
    }
  };

  const remove = async (p: OvertimeProfile) => {
    if (!window.confirm(`¿Eliminar perfil de ${p.empleado_nombre ?? p.empleado}?`)) return;
    try {
      await api.delete(`/api/payroll/overtime/profiles/${p.id}/`);
      await fetchAll();
      if (editingId === p.id) resetForm();
    } catch {
      setError('No se pudo eliminar el perfil.');
    }
  };

  return (
    <GlassCard padding="md">
      <h3 className="overtime-section-title">Perfiles de Tiempo Extra</h3>
      {error && (
        <ErrorState
          title="Error"
          message={error}
          action={
            <Button variant="secondary" size="sm" onClick={() => setError(null)}>
              Cerrar
            </Button>
          }
        />
      )}

      {canEdit && (
        <div className="overtime-profile-form">
          <div className="overtime-profile-form-row">
            <label className="overtime-profile-field">
              <span>Empleado</span>
              <select
                className="overtime-profile-select"
                value={draft.empleado}
                onChange={e => {
                  const no = e.target.value;
                  setDraft(prev => ({
                    ...prev,
                    empleado: no,
                    empleado_nombre: employeesById[no] ?? '',
                  }));
                }}
                disabled={editingId !== null}
              >
                <option value="">— Selecciona —</option>
                {employeeOptions.map(e => (
                  <option key={e.no_nomina} value={e.no_nomina}>
                    {e.no_nomina} — {e.nombre}
                  </option>
                ))}
              </select>
            </label>

            <label className="overtime-profile-field">
              <span>Tipo de perfil</span>
              <select
                className="overtime-profile-select"
                value={draft.profile_type}
                onChange={e => setDraft(prev => ({ ...prev, profile_type: e.target.value }))}
              >
                {PROFILE_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </label>

            <label className="overtime-profile-field overtime-profile-checkbox">
              <input
                type="checkbox"
                checked={draft.is_active}
                onChange={e => setDraft(prev => ({ ...prev, is_active: e.target.checked }))}
              />
              <span>Activo</span>
            </label>
          </div>

          {draft.profile_type === 'FIXED_CUSTOM' && (
            <div className="overtime-profile-form-row">
              <div className="overtime-profile-field">
                <span>Días (lun-sáb)</span>
                <div className="overtime-weekday-toggles">
                  {WEEKDAY_LABELS.map((lbl, idx) => (
                    <button
                      key={lbl}
                      type="button"
                      className={`overtime-weekday-btn${
                        draft.custom_weekdays.includes(idx) ? ' active' : ''
                      }`}
                      onClick={() => toggleWeekday(idx)}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
              </div>
              <label className="overtime-profile-field">
                <span>Horas por día</span>
                <input
                  type="number"
                  min="0.5"
                  step="0.5"
                  className="overtime-profile-input"
                  value={draft.custom_daily_hours}
                  onChange={e =>
                    setDraft(prev => ({ ...prev, custom_daily_hours: e.target.value }))
                  }
                />
              </label>
            </div>
          )}

          <div className="overtime-profile-actions">
            <Button variant="primary" size="sm" onClick={save} disabled={saving}>
              <FloppyDisk weight="bold" /> {editingId !== null ? 'Actualizar' : 'Crear'}
            </Button>
            {editingId !== null && (
              <Button variant="ghost" size="sm" onClick={resetForm}>
                Cancelar
              </Button>
            )}
          </div>
        </div>
      )}

      <div className="overtime-profile-search">
        <MagnifyingGlass size={16} />
        <input
          type="text"
          placeholder="Buscar por número o nombre..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="overtime-profile-table-wrapper">
        <table className="overtime-profile-table">
          <thead>
            <tr>
              <th>No.</th>
              <th>Nombre</th>
              <th>Tipo</th>
              <th>Días custom</th>
              <th>Horas custom</th>
              <th>Activo</th>
              {canEdit && <th></th>}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={canEdit ? 7 : 6}>Cargando…</td></tr>
            )}
            {!loading && filteredProfiles.length === 0 && (
              <tr><td colSpan={canEdit ? 7 : 6}>Sin perfiles.</td></tr>
            )}
            {filteredProfiles.map(p => (
              <tr key={p.id}>
                <td>{p.empleado}</td>
                <td>{p.empleado_nombre ?? employeesById[p.empleado] ?? '—'}</td>
                <td>{PROFILE_TYPES.find(t => t.value === p.profile_type)?.label ?? p.profile_type}</td>
                <td>
                  {p.profile_type === 'FIXED_CUSTOM'
                    ? (p.custom_weekdays ?? []).map(d => WEEKDAY_LABELS[d]).join(', ')
                    : '—'}
                </td>
                <td>{p.profile_type === 'FIXED_CUSTOM' ? p.custom_daily_hours ?? '—' : '—'}</td>
                <td>{p.is_active ? 'Sí' : 'No'}</td>
                {canEdit && (
                  <td className="overtime-profile-actions-cell">
                    <Button variant="ghost" size="sm" onClick={() => startEdit(p)}>
                      Editar
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => remove(p)}>
                      <Trash weight="bold" />
                    </Button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
};

export default OvertimeProfileManager;
