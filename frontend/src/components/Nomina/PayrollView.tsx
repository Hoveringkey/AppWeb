import React from 'react';
import PayrollReport from '../PayrollReport';
import { PageShell } from '../ui';
import '../modules.css';
import '../Dashboard.css'; // reuse submit-button, ag-grid styles, etc.
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

const PayrollView: React.FC = () => {
  return (
    <PageShell
      title="Calcular Nómina"
      description="Ejecuta el reporte de variaciones por semana. Previsualiza antes de cerrar el período."
    >
      <PayrollReport />
    </PageShell>
  );
};

export default PayrollView;
