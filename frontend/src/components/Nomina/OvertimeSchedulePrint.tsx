import React from 'react';

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

const cellLabel = (a?: PrintAssignment) => {
  if (!a) return '';
  if (a.assignment_type === 'TIPO_1') return a.compensation_type === 'TXT' ? 'TxT 8h' : '1º';
  if (a.assignment_type === 'TIPO_2') return a.compensation_type === 'TXT' ? 'TxT 4h' : '2º';
  return `${a.compensation_type === 'TXT' ? 'TxT' : 'Cust'} ${parseFloat(a.hours).toFixed(1)}h`;
};

const OvertimeSchedulePrint: React.FC<PrintProps> = ({ isoYear, isoWeek, weekDates, rows }) => (
  <div className="overtime-print-only">
    <h2 className="overtime-print-title">
      Programación Tiempo Extra — Semana {isoYear}-W{isoWeek}
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
  </div>
);

export default OvertimeSchedulePrint;
