import React, { useEffect, useMemo, useRef, useState } from 'react';
import { MagnifyingGlass, FloppyDisk, Trash, CaretDown } from '@phosphor-icons/react';
import api from '../../api/axios';
import { Button, GlassCard, ErrorState } from '../ui';

const PROFILE_TYPES: Array<{ value: string; label: string }> = [
  { value: 'ROTATION_A', label: 'Rotación A (lun-mié / mar-jue)' },
  { value: 'ROTATION_B', label: 'Rotación B (mar-jue / lun-mié)' },
  { value: 'SATURDAY_OR_MONDAY_8H', label: 'Sábado o Lunes 8h' },
  { value: 'FIXED_4DAY', label: 'Fijo Lunes a Jueves' },
  { value: 'FIXED_CUSTOM', label: 'Personalizado' },
];

const WEEKDAY_LABELS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const LEGACY_SATURDAY_MONDAY = 'SATURDAY_MONDAY_8H';
const SATURDAY_OR_MONDAY = 'SATURDAY_OR_MONDAY_8H';

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

const normalizeProfileType = (t: string): string =>
  t === LEGACY_SATURDAY_MONDAY ? SATURDAY_OR_MONDAY : t;

const OvertimeProfileManager: React.FC<{ canEdit: boolean }> = ({ canEdit }) => {
  const [profiles, setProfiles] = useState<OvertimeProfile[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [draft, setDraft] = useState<DraftState>(emptyDraft());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  // Combobox de empleado
  const [empSearch, setEmpSearch] = useState('');
  const [empOpen, setEmpOpen] = useState(false);
  const empBlurTimer = useRef<number | null>(null);

  // Dropdown de tipo de perfil
  const [typeOpen, setTypeOpen] = useState(false);
  const typeBlurTimer = useRef<number | null>(null);

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

  const filteredEmployeeOptions = useMemo(() => {
    const q = empSearch.trim().toLowerCase();
    if (!q) return employeeOptions;
    return employeeOptions.filter(e =>
      e.no_nomina.toLowerCase().includes(q) ||
      e.nombre.toLowerCase().includes(q)
    );
  }, [employeeOptions, empSearch]);

  const toggleWeekday = (idx: number) => {
    setDraft(prev => {
      const next = new Set(prev.custom_weekdays);
      if (next.has(idx)) next.delete(idx); else next.add(idx);
      return { ...prev, custom_weekdays: Array.from(next).sort((a, b) => a - b) };
    });
  };

  const setSaturdayOrMondayDay = (day: 0 | 5) => {
    setDraft(prev => ({ ...prev, custom_weekdays: [day], custom_daily_hours: '' }));
  };

  const selectEmployee = (e: Employee) => {
    setDraft(prev => ({ ...prev, empleado: e.no_nomina, empleado_nombre: e.nombre }));
    setEmpSearch('');
    setEmpOpen(false);
  };

  const onEmpInputChange = (value: string) => {
    // Si ya había selección, limpiarla cuando el usuario empieza a escribir.
    if (draft.empleado) {
      setDraft(prev => ({ ...prev, empleado: '', empleado_nombre: '' }));
    }
    setEmpSearch(value);
    setEmpOpen(true);
  };

  const onEmpBlur = () => {
    empBlurTimer.current = window.setTimeout(() => setEmpOpen(false), 150);
  };
  const onEmpFocus = () => {
    if (empBlurTimer.current !== null) {
      window.clearTimeout(empBlurTimer.current);
      empBlurTimer.current = null;
    }
    setEmpOpen(true);
  };

  const selectProfileType = (value: string) => {
    setDraft(prev => ({
      ...prev,
      profile_type: value,
      // Reset campos dependientes para no arrastrar basura de un tipo a otro.
      custom_weekdays: [],
      custom_daily_hours: '',
    }));
    setTypeOpen(false);
  };

  const onTypeBlur = () => {
    typeBlurTimer.current = window.setTimeout(() => setTypeOpen(false), 150);
  };
  const onTypeFocus = () => {
    if (typeBlurTimer.current !== null) {
      window.clearTimeout(typeBlurTimer.current);
      typeBlurTimer.current = null;
    }
  };

  const currentTypeLabel = useMemo(() => {
    const found = PROFILE_TYPES.find(t => t.value === draft.profile_type);
    return found ? found.label : draft.profile_type;
  }, [draft.profile_type]);

  const startEdit = (p: OvertimeProfile) => {
    const normalizedType = normalizeProfileType(p.profile_type);
    let weekdays = Array.isArray(p.custom_weekdays) ? [...p.custom_weekdays] : [];
    if (normalizedType === SATURDAY_OR_MONDAY) {
      // Garantiza que el formulario abra con una selección válida (default Sábado).
      if (weekdays.length !== 1 || (weekdays[0] !== 0 && weekdays[0] !== 5)) {
        weekdays = [5];
      }
    }
    setEditingId(p.id);
    setDraft({
      empleado: p.empleado,
      empleado_nombre: p.empleado_nombre ?? employeesById[p.empleado] ?? '',
      profile_type: normalizedType,
      custom_weekdays: weekdays,
      custom_daily_hours: p.custom_daily_hours ?? '',
      is_active: p.is_active,
    });
    setEmpSearch('');
    setEmpOpen(false);
  };

  const resetForm = () => {
    setEditingId(null);
    setDraft(emptyDraft());
    setEmpSearch('');
    setEmpOpen(false);
  };

  const save = async () => {
    if (!draft.empleado) {
      setError('Selecciona un empleado.');
      return;
    }
    if (
      draft.profile_type === SATURDAY_OR_MONDAY &&
      (draft.custom_weekdays.length !== 1 ||
        (draft.custom_weekdays[0] !== 0 && draft.custom_weekdays[0] !== 5))
    ) {
      setError('Selecciona Lunes o Sábado.');
      return;
    }
    setSaving(true);
    setError(null);
    const isCustom = draft.profile_type === 'FIXED_CUSTOM';
    const isSatOrMon = draft.profile_type === SATURDAY_OR_MONDAY;
    const payload: Record<string, unknown> = {
      empleado: draft.empleado,
      profile_type: draft.profile_type,
      is_active: draft.is_active,
      custom_weekdays: isCustom
        ? draft.custom_weekdays
        : isSatOrMon
          ? draft.custom_weekdays
          : [],
      custom_daily_hours: isCustom ? (draft.custom_daily_hours || '0') : null,
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

  const empInputValue = draft.empleado
    ? `${draft.empleado} — ${draft.empleado_nombre}`
    : empSearch;

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
              <div className="overtime-profile-combobox">
                <input
                  type="text"
                  className="overtime-profile-combobox-input"
                  placeholder="Buscar empleado por número o nombre..."
                  value={empInputValue}
                  onChange={e => onEmpInputChange(e.target.value)}
                  onFocus={onEmpFocus}
                  onBlur={onEmpBlur}
                  disabled={editingId !== null}
                  autoComplete="off"
                />
                {empOpen && editingId === null && (
                  <ul className="overtime-profile-combobox-list">
                    {filteredEmployeeOptions.length === 0 && (
                      <li className="overtime-profile-combobox-empty">
                        Sin coincidencias
                      </li>
                    )}
                    {filteredEmployeeOptions.slice(0, 50).map(e => (
                      <li
                        key={e.no_nomina}
                        className="overtime-profile-combobox-option"
                        onMouseDown={ev => ev.preventDefault()}
                        onClick={() => selectEmployee(e)}
                      >
                        <span className="overtime-profile-combobox-option-num">
                          {e.no_nomina}
                        </span>
                        <span className="overtime-profile-combobox-option-sep">—</span>
                        <span className="overtime-profile-combobox-option-name">
                          {e.nombre}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </label>

            <label className="overtime-profile-field">
              <span>Tipo de perfil</span>
              <div className="overtime-profile-typeselect">
                <button
                  type="button"
                  className="overtime-profile-typeselect-trigger"
                  onClick={() => setTypeOpen(o => !o)}
                  onBlur={onTypeBlur}
                  onFocus={onTypeFocus}
                >
                  <span>{currentTypeLabel}</span>
                  <CaretDown size={14} weight="bold" />
                </button>
                {typeOpen && (
                  <ul
                    className="overtime-profile-typeselect-list"
                    onMouseDown={ev => ev.preventDefault()}
                  >
                    {PROFILE_TYPES.map(t => (
                      <li
                        key={t.value}
                        className={`overtime-profile-typeselect-option${
                          t.value === draft.profile_type ? ' active' : ''
                        }`}
                        onClick={() => selectProfileType(t.value)}
                      >
                        {t.label}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
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

          {draft.profile_type === SATURDAY_OR_MONDAY && (
            <div className="overtime-profile-form-row">
              <div className="overtime-profile-field">
                <span>Día de 8 horas</span>
                <div className="overtime-weekday-toggles">
                  <button
                    type="button"
                    className={`overtime-weekday-btn${
                      draft.custom_weekdays[0] === 0 ? ' active' : ''
                    }`}
                    onClick={() => setSaturdayOrMondayDay(0)}
                  >
                    Lunes
                  </button>
                  <button
                    type="button"
                    className={`overtime-weekday-btn${
                      draft.custom_weekdays[0] === 5 ? ' active' : ''
                    }`}
                    onClick={() => setSaturdayOrMondayDay(5)}
                  >
                    Sábado
                  </button>
                </div>
              </div>
            </div>
          )}

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
            {filteredProfiles.map(p => {
              const normalized = normalizeProfileType(p.profile_type);
              const typeLabel =
                PROFILE_TYPES.find(t => t.value === normalized)?.label ?? p.profile_type;
              let daysLabel: string = '—';
              if (normalized === 'FIXED_CUSTOM') {
                daysLabel = (p.custom_weekdays ?? []).map(d => WEEKDAY_LABELS[d]).join(', ');
              } else if (normalized === SATURDAY_OR_MONDAY) {
                const d = (p.custom_weekdays ?? [])[0];
                daysLabel = d === 0 ? 'Lun' : d === 5 ? 'Sáb' : '—';
              }
              const hoursLabel = normalized === 'FIXED_CUSTOM'
                ? (p.custom_daily_hours ?? '—')
                : normalized === SATURDAY_OR_MONDAY
                  ? '8.00'
                  : '—';
              return (
                <tr key={p.id}>
                  <td>{p.empleado}</td>
                  <td>{p.empleado_nombre ?? employeesById[p.empleado] ?? '—'}</td>
                  <td>{typeLabel}</td>
                  <td>{daysLabel}</td>
                  <td>{hoursLabel}</td>
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
              );
            })}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
};

export default OvertimeProfileManager;
