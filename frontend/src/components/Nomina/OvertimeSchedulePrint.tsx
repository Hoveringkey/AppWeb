import React from 'react';
import { formatHoursLabel, monthNameEs } from './overtimeFormat';

interface PrintAssignment {
  empleado: string;
  fecha: string;
  assignment_type: 'TIPO_1' | 'TIPO_2' | 'CUSTOM';
  hours: string;
  compensation_type: 'PAYROLL' | 'TXT';
}

interface PrintProps {
  isoYear: number;
  isoWeek: number;
  weekDates: string[];
  rows: Array<{
    no_nomina: string;
    nombre: string;
    cells: Record<string, PrintAssignment | undefined>;
  }>;
}

const DAY_LABELS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

const cellLabel = (a?: PrintAssignment) => (a ? formatHoursLabel(a.hours) : '');

const OvertimeSchedulePrint: React.FC<PrintProps> = ({ isoWeek, weekDates, rows }) => {
  const monthName = weekDates[0] ? monthNameEs(weekDates[0]) : '';
  return (
    <div className="overtime-print-only">
      <h2 className="overtime-print-title">
        Programación Tiempo Extra — {monthName} S{isoWeek}
      </h2>
      <table className="overtime-print-table">
        <thead>
          <tr>
            <th>No. Nóm.</th>
            <th>Nombre</th>
            {weekDates.map((d, i) => (
              <th key={d}>
                {DAY_LABELS[i]} {d.slice(8, 10)}
              </th>
            ))}
            <th className="overtime-print-signature">Firma</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.no_nomina}>
              <td>{r.no_nomina}</td>
              <td>{r.nombre}</td>
              {weekDates.map(d => (
                <td key={d}>{cellLabel(r.cells[d])}</td>
              ))}
              <td className="overtime-print-signature"></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="overtime-print-policy">
        Política: si un empleado falta o tiene permiso sin goce, pierde el derecho a tiempo extra durante la siguiente semana.
      </p>
    </div>
  );
};

export default OvertimeSchedulePrint;
