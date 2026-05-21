import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowClockwise,
  Lightning,
  PaperPlaneTilt,
  Printer,
  CheckCircle,
} from '@phosphor-icons/react';
import api from '../../api/axios';
import { useAuth } from '../../auth/AuthContext';
import { Button, ErrorState, GlassCard, PageShell } from '../ui';
import OvertimeSchedulePrint from './OvertimeSchedulePrint';
import OvertimeProfileManager from './OvertimeProfileManager';
import '../modules.css';
import '../Dashboard.css';
import './Nomina.css';

type Compensation = 'PAYROLL' | 'TXT';
type AssignmentType = 'TIPO_1' | 'TIPO_2' | 'CUSTOM';
type ScheduleStatus = 'DRAFT' | 'PUBLISHED' | 'LOCKED';

interface OvertimeAssignment {
  id: number;
  schedule: number;
  empleado: string;
  empleado_nombre?: string;
  fecha: string;
  assignment_type: AssignmentType;
  hours: string;
  compensation_type: Compensation;
  source: 'AUTO' | 'MANUAL';
  is_forced: boolean;
}

interface Penalty {
  id: number;
  empleado: string;
  empleado_nombre?: string;
  reason: string;
  source_incidence_date: string;
}

interface Schedule {
  id: number;
  iso_year: number;
  iso_week: number;
  status: ScheduleStatus;
  published_at: string | null;
  locked_at: string | null;
  notes: string;
  assignments: OvertimeAssignment[];
  penalties: Penalty[];
  week_dates: string[];
}

interface CycleStep {
  assignment_type: AssignmentType;
  hours: string;
  compensation_type: Compensation;
  label: string;
}

const CYCLE: CycleStep[] = [
  { assignment_type: 'TIPO_2', hours: '4.00', compensation_type: 'PAYROLL', label: '2º' },
  { assignment_type: 'CUSTOM', hours: '4.00', compensation_type: 'TXT', label: 'TxT' },
];

const DAY_LABELS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

// Devuelve el índice del paso actual en CYCLE, o -1 si la asignación
// no es ciclable (e.g. TIPO_1 heredada del perfil SATURDAY_OR_MONDAY_8H).
const matchStep = (a: OvertimeAssignment): number => {
  if (a.assignment_type === 'TIPO_2' && a.compensation_type === 'PAYROLL') return 0;
  if (a.compensation_type === 'TXT') return 1;
  return -1;
};

const getCellLabel = (a: OvertimeAssignment): string => {
  if (a.assignment_type === 'TIPO_1' && a.compensation_type === 'PAYROLL') return '1º';
  if (a.assignment_type === 'TIPO_2' && a.compensation_type === 'PAYROLL') return '2º';
  if (a.compensation_type === 'TXT') return 'TxT';
  if (a.assignment_type === 'CUSTOM' && a.compensation_type === 'PAYROLL') {
    const h = parseFloat(a.hours);
    return `Cust ${Number.isFinite(h) ? h : a.hours}h`;
  }
  return '';
};

interface RowData {
  empleado: string;
  empleado_nombre: string;
  cells: Record<string, OvertimeAssignment | undefined>;
  penalty?: Penalty;
}

const OvertimeScheduleView: React.FC = () => {
  const { user, hasPermission, hasGroup } = useAuth();
  const canEdit = useMemo(
    () => Boolean(user?.is_superuser || hasPermission('can_capture_hr') || hasPermission('can_manage_payroll') || hasGroup(['HR_CAPTURE', 'FINANCE_ADMIN'])),
    [user, hasPermission, hasGroup]
  );

  const [isoYear, setIsoYear] = useState<number | ''>('');
  const [isoWeek, setIsoWeek] = useState<number | ''>('');
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyCellKey, setBusyCellKey] = useState<string | null>(null);
  const [showProfiles, setShowProfiles] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await api.get('/api/payroll/current-week/');
        if (cancelled) return;
        setIsoYear(resp.data.current_iso_year);
        setIsoWeek(resp.data.current_week);
      } catch {
        // no-op
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const loadSchedule = useCallback(async (year: number, week: number) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await api.get('/api/payroll/overtime/schedules/', {
        params: { iso_year: year, iso_week: week },
      });
      const data = Array.isArray(resp.data) ? resp.data : resp.data?.results;
      const found = data?.find(
        (s: Schedule) => s.iso_year === year && s.iso_week === week
      );
      setSchedule(found ?? null);
    } catch {
      setError('No se pudo cargar la planilla.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (typeof isoYear !== 'number' || typeof isoWeek !== 'number') return;
    const id = window.setTimeout(() => {
      void loadSchedule(isoYear, isoWeek);
    }, 0);
    return () => window.clearTimeout(id);
  }, [isoYear, isoWeek, loadSchedule]);

  const extractErrorMessage = (err: unknown): string => {
    const ax = err as { response?: { status?: number; data?: { detail?: string } } };
    if (ax.response?.status === 409) {
      return ax.response?.data?.detail ?? 'Conflicto (409): la semana está cerrada o la planilla bloqueada.';
    }
    return ax.response?.data?.detail ?? 'Error de operación.';
  };

  const generate = async () => {
    if (typeof isoYear !== 'number' || typeof isoWeek !== 'number') return;
    setLoading(true);
    setError(null);
    try {
      const resp = await api.post('/api/payroll/overtime/schedules/generate/', {
        iso_year: isoYear, iso_week: isoWeek,
      });
      setSchedule(resp.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const publish = async () => {
    if (!schedule) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await api.post(`/api/payroll/overtime/schedules/${schedule.id}/publish/`);
      setSchedule({ ...schedule, ...resp.data, assignments: schedule.assignments, penalties: schedule.penalties });
      await loadSchedule(schedule.iso_year, schedule.iso_week);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const applyToIncidences = async () => {
    if (!schedule) return;
    if (!window.confirm('¿Aplicar planilla a incidencias HX? Esto la bloqueará.')) return;
    setLoading(true);
    setError(null);
    try {
      await api.post(`/api/payroll/overtime/schedules/${schedule.id}/apply-to-incidences/`);
      await loadSchedule(schedule.iso_year, schedule.iso_week);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const rows: RowData[] = useMemo(() => {
    if (!schedule) return [];
    const map: Record<string, RowData> = {};
    for (const a of schedule.assignments) {
      if (!map[a.empleado]) {
        map[a.empleado] = {
          empleado: a.empleado,
          empleado_nombre: a.empleado_nombre ?? a.empleado,
          cells: {},
        };
      }
      map[a.empleado].cells[a.fecha] = a;
    }
    for (const p of schedule.penalties) {
      if (!map[p.empleado]) {
        map[p.empleado] = {
          empleado: p.empleado,
          empleado_nombre: p.empleado_nombre ?? p.empleado,
          cells: {},
        };
      }
      map[p.empleado].penalty = p;
    }
    return Object.values(map).sort((a, b) => a.empleado.localeCompare(b.empleado));
  }, [schedule]);

  const cycleCell = async (row: RowData, fecha: string) => {
    if (!schedule || schedule.status !== 'DRAFT') return;
    const current = row.cells[fecha];
    const forced = Boolean(row.penalty);
    const key = `${row.empleado}-${fecha}`;
    setBusyCellKey(key);
    setError(null);
    try {
      if (!current) {
        const step = CYCLE[0];
        await api.post('/api/payroll/overtime/assignments/', {
          schedule: schedule.id,
          empleado: row.empleado,
          fecha,
          assignment_type: step.assignment_type,
          hours: step.hours,
          compensation_type: step.compensation_type,
          is_forced: forced,
        });
      } else {
        const idx = matchStep(current);
        if (idx < 0) {
          // Fuera del ciclo manual (TIPO_1 del perfil sábado/lunes, CUSTOM PAYROLL legacy):
          // un click la borra directamente.
          await api.delete(`/api/payroll/overtime/assignments/${current.id}/`);
        } else {
          const nextIdx = idx + 1;
          if (nextIdx >= CYCLE.length) {
            await api.delete(`/api/payroll/overtime/assignments/${current.id}/`);
          } else {
            const step = CYCLE[nextIdx];
            await api.patch(`/api/payroll/overtime/assignments/${current.id}/`, {
              assignment_type: step.assignment_type,
              hours: step.hours,
              compensation_type: step.compensation_type,
            });
          }
        }
      }
      await loadSchedule(schedule.iso_year, schedule.iso_week);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusyCellKey(null);
    }
  };

  const printedRows = rows.map(r => ({
    no_nomina: r.empleado,
    nombre: r.empleado_nombre,
    cells: r.cells,
  }));

  const isDraft = schedule?.status === 'DRAFT';
  const isPublished = schedule?.status === 'PUBLISHED';
  const isLocked = schedule?.status === 'LOCKED';

  return (
    <PageShell
      title="Programar Tiempo Extra"
      description="Planifica el tiempo extra semanal por empleado (rotaciones, días fijos y excepciones)."
      actions={
        <Button variant="ghost" size="sm" onClick={() => setShowProfiles(s => !s)}>
          {showProfiles ? 'Ocultar' : 'Administrar'} perfiles
        </Button>
      }
    >
      <div className="overtime-screen-grid">
        {showProfiles && <OvertimeProfileManager canEdit={canEdit} />}

        <GlassCard padding="md">
          <div className="overtime-toolbar">
            <div className="overtime-toolbar-fields">
              <label>
                Año ISO
                <input
                  type="number"
                  className="pr-week-input"
                  value={isoYear}
                  onChange={e => setIsoYear(e.target.value ? Number(e.target.value) : '')}
                />
              </label>
              <label>
                Semana ISO
                <input
                  type="number"
                  min={1}
                  max={53}
                  className="pr-week-input"
                  value={isoWeek}
                  onChange={e => setIsoWeek(e.target.value ? Number(e.target.value) : '')}
                />
              </label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  typeof isoYear === 'number' && typeof isoWeek === 'number' && loadSchedule(isoYear, isoWeek)
                }
                disabled={loading}
              >
                <ArrowClockwise weight="bold" /> Cargar
              </Button>
            </div>

            <div className="overtime-toolbar-actions">
              {schedule && (
                <span className={`overtime-status-badge overtime-status-${schedule.status}`}>
                  {schedule.status}
                </span>
              )}
              {canEdit && (
                <>
                  <Button variant="primary" size="sm" onClick={generate} disabled={loading}>
                    <Lightning weight="bold" /> Generar
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={publish}
                    disabled={loading || !isDraft}
                  >
                    <PaperPlaneTilt weight="bold" /> Publicar
                  </Button>
                  <Button
                    variant="success"
                    size="sm"
                    onClick={applyToIncidences}
                    disabled={loading || !isPublished}
                  >
                    <CheckCircle weight="bold" /> Aplicar a incidencias
                  </Button>
                </>
              )}
              <Button variant="ghost" size="sm" onClick={() => window.print()} disabled={!schedule}>
                <Printer weight="bold" /> Imprimir
              </Button>
            </div>
          </div>
        </GlassCard>

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

        <GlassCard padding="md">
          {!schedule && !loading && (
            <div className="pr-prompt">
              No hay planilla cargada para esta semana. Pulsa <b>Generar</b> para crearla.
            </div>
          )}

          {schedule && (
            <div className="overtime-grid-wrapper">
              <table className="overtime-grid">
                <thead>
                  <tr>
                    <th>No.</th>
                    <th>Empleado</th>
                    {schedule.week_dates.map((d, idx) => (
                      <th key={d}>
                        <div>{DAY_LABELS[idx]}</div>
                        <div className="overtime-grid-date">{d.slice(5)}</div>
                      </th>
                    ))}
                    <th>Nómina</th>
                    <th>TxT</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 && (
                    <tr>
                      <td colSpan={schedule.week_dates.length + 4}>
                        Sin filas. Genera la planilla o registra perfiles.
                      </td>
                    </tr>
                  )}
                  {rows.map(r => {
                    let payrollHours = 0;
                    let txtHours = 0;
                    Object.values(r.cells).forEach(a => {
                      if (!a) return;
                      const h = parseFloat(a.hours);
                      if (a.compensation_type === 'PAYROLL') payrollHours += h;
                      else txtHours += h;
                    });
                    return (
                      <tr
                        key={r.empleado}
                        className={r.penalty ? 'overtime-row-penalized' : ''}
                        title={r.penalty ? `Penalizado: ${r.penalty.reason} (${r.penalty.source_incidence_date})` : ''}
                      >
                        <td>{r.empleado}</td>
                        <td>{r.empleado_nombre}</td>
                        {schedule.week_dates.map(d => {
                          const a = r.cells[d];
                          const key = `${r.empleado}-${d}`;
                          const readOnly = !isDraft || !canEdit;
                          const label = a
                            ? getCellLabel(a) + (a.is_forced ? '*' : '')
                            : '';
                          return (
                            <td
                              key={d}
                              className={`overtime-cell${readOnly ? ' overtime-cell-readonly' : ''}${a ? ' overtime-cell-filled' : ''}${a?.compensation_type === 'TXT' ? ' overtime-cell-txt' : ''}`}
                              onClick={() => !readOnly && busyCellKey !== key && cycleCell(r, d)}
                            >
                              {label}
                            </td>
                          );
                        })}
                        <td className="overtime-grid-total">{payrollHours.toFixed(1)}</td>
                        <td className="overtime-grid-total">{txtHours.toFixed(1)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {(isPublished || isLocked) && (
                <p className="overtime-grid-note">
                  La planilla está {isLocked ? 'bloqueada' : 'publicada'}; las celdas son de solo lectura.
                </p>
              )}
            </div>
          )}
        </GlassCard>

        {schedule && (
          <OvertimeSchedulePrint
            isoYear={schedule.iso_year}
            isoWeek={schedule.iso_week}
            weekDates={schedule.week_dates}
            rows={printedRows}
          />
        )}
      </div>
    </PageShell>
  );
};

export default OvertimeScheduleView;
