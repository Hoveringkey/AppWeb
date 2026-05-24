/**
 * payrollExport.ts
 *
 * Builds a polished XLSX of the live-calculated payroll preview and triggers a
 * browser download.  Reuses buildTokens() so the "Resumen operativo" column
 * mirrors the on-screen pills exactly (just without colour).
 */

import ExcelJS from 'exceljs';
import { buildTokens, type DesgloseRow } from './GridRenderers';

interface ExportOptions {
  week: number;
  year: number;
}

const MONEY_FMT = '"$"#,##0.00;-"$"#,##0.00';
const HOURS_FMT = '0.00';

const HEADER_BG    = 'FF1F2937';
const HEADER_BORDER = 'FF374151';
const TITLE_COLOR  = 'FF1F2937';
const SUBTLE_COLOR = 'FF6B7280';
const FAINT_COLOR  = 'FF9CA3AF';
const ROW_BORDER   = 'FFE5E7EB';
const ZEBRA_BG     = 'FFF9FAFB';

const COLUMNS: Array<{ header: string; key: string; width: number }> = [
  { header: 'No. Nómina',          key: 'no_nomina',         width: 14 },
  { header: 'Nombre',              key: 'nombre',            width: 32 },
  { header: 'Resumen operativo',   key: 'resumen',           width: 60 },
  { header: 'Ausentismos',         key: 'ausentismos',       width: 45 },
  { header: 'Bono nocturno',       key: 'bono_nocturno',     width: 18 },
  { header: 'Bono mensual',        key: 'bono_mensual',      width: 18 },
  { header: 'Bono abastecedor',    key: 'bono_abastecedor',  width: 18 },
  { header: 'Horas extra pagadas', key: 'paid_extra_hours',  width: 18 },
  { header: 'Descuento préstamo',  key: 'loan_deduction',    width: 18 },
  { header: 'Progreso préstamo',   key: 'progreso_prestamo', width: 18 },
];

const MONEY_KEYS = new Set([
  'bono_nocturno',
  'bono_mensual',
  'bono_abastecedor',
  'loan_deduction',
]);

export async function exportPayrollXlsx(
  rows: DesgloseRow[],
  options: ExportOptions,
): Promise<void> {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'Axis';
  workbook.created = new Date();

  const ws = workbook.addWorksheet(`Nómina S${options.week} ${options.year}`, {
    views: [{ state: 'frozen', ySplit: 5 }],
  });

  // Column definitions (widths + keys).  Headers will be written manually in
  // row 5 so they don't collide with the merged title rows above.
  ws.columns = COLUMNS.map(c => ({ key: c.key, width: c.width }));

  // ── Rows 1-4: title block ──────────────────────────────────────────────
  ws.mergeCells('A1:J1');
  const titleCell = ws.getCell('A1');
  titleCell.value = 'Reporte de Nómina';
  titleCell.font = { name: 'Calibri', size: 18, bold: true, color: { argb: TITLE_COLOR } };
  titleCell.alignment = { vertical: 'middle', horizontal: 'left' };
  ws.getRow(1).height = 30;

  ws.mergeCells('A2:J2');
  const subtitleCell = ws.getCell('A2');
  subtitleCell.value = `Semana ${options.week} · Año ISO ${options.year}`;
  subtitleCell.font = { name: 'Calibri', size: 11, color: { argb: SUBTLE_COLOR } };
  subtitleCell.alignment = { vertical: 'middle', horizontal: 'left' };

  ws.mergeCells('A3:J3');
  const countCell = ws.getCell('A3');
  countCell.value = `Empleados con variaciones: ${rows.length}`;
  countCell.font = { name: 'Calibri', size: 11, color: { argb: SUBTLE_COLOR } };
  countCell.alignment = { vertical: 'middle', horizontal: 'left' };

  ws.mergeCells('A4:J4');
  const dateCell = ws.getCell('A4');
  dateCell.value = `Generado: ${new Date().toLocaleString('es-MX')}`;
  dateCell.font = { name: 'Calibri', size: 10, italic: true, color: { argb: FAINT_COLOR } };
  dateCell.alignment = { vertical: 'middle', horizontal: 'left' };

  // ── Row 5: column headers ──────────────────────────────────────────────
  const headerRow = ws.getRow(5);
  headerRow.values = COLUMNS.map(c => c.header);
  headerRow.height = 28;
  headerRow.eachCell({ includeEmpty: false }, cell => {
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: HEADER_BG } };
    cell.font = { name: 'Calibri', bold: true, size: 11, color: { argb: 'FFFFFFFF' } };
    cell.alignment = { vertical: 'middle', horizontal: 'left', wrapText: true };
    cell.border = {
      bottom: { style: 'thin', color: { argb: HEADER_BORDER } },
    };
  });

  // ── Data rows (start at row 6) ─────────────────────────────────────────
  rows.forEach((row, i) => {
    const resumen = buildTokens(row).map(t => t.label).join(' | ');
    const ausentismos = row.ausentismos || '';
    const progresoPrestamo =
      row.total_pagos > 0 ? `${row.pagos_realizados}/${row.total_pagos}` : '';

    const dataRow = ws.addRow({
      no_nomina:         row.no_nomina,
      nombre:            row.nombre,
      resumen,
      ausentismos,
      bono_nocturno:     row.bonos?.Nocturno ?? 0,
      bono_mensual:      row.bonos?.Mensual ?? 0,
      bono_abastecedor:  row.bonos?.Abastecedor ?? 0,
      paid_extra_hours:  row.paid_extra_hours ?? 0,
      loan_deduction:    row.loan_deduction ?? 0,
      progreso_prestamo: progresoPrestamo,
    });

    // Dynamic row height (clamped) so wrapped resumen/ausentismos stay readable.
    const maxLen = Math.max(resumen.length, ausentismos.length);
    dataRow.height = Math.min(60, Math.max(22, Math.ceil(maxLen / 60) * 18));

    const isZebra = i % 2 === 1;

    dataRow.eachCell({ includeEmpty: false }, (cell, colNumber) => {
      const colKey = COLUMNS[colNumber - 1]?.key;
      const wrap = colKey === 'resumen' || colKey === 'ausentismos';

      cell.alignment = {
        vertical: 'middle',
        horizontal: wrap ? 'left' : 'left',
        wrapText: wrap,
      };
      cell.border = {
        top:    { style: 'thin', color: { argb: ROW_BORDER } },
        left:   { style: 'thin', color: { argb: ROW_BORDER } },
        bottom: { style: 'thin', color: { argb: ROW_BORDER } },
        right:  { style: 'thin', color: { argb: ROW_BORDER } },
      };
      if (isZebra) {
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: ZEBRA_BG } };
      }
      cell.font = { name: 'Calibri', size: 11, color: { argb: 'FF111827' } };

      if (colKey && MONEY_KEYS.has(colKey)) {
        cell.numFmt = MONEY_FMT;
      } else if (colKey === 'paid_extra_hours') {
        cell.numFmt = HOURS_FMT;
      }
    });
  });

  // ── Autofilter on header row ───────────────────────────────────────────
  ws.autoFilter = {
    from: { row: 5, column: 1 },
    to:   { row: 5, column: COLUMNS.length },
  };

  // ── Write + download ───────────────────────────────────────────────────
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer as BlobPart], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `nomina_semana_${options.week}_anio_${options.year}.xlsx`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
