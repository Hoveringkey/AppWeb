from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet,
    IncidenceCatalogViewSet,
    IncidenceRecordViewSet,
    LoanViewSet,
    ExtraHourBankViewSet,
    PayrollSnapshotViewSet,
    CalculatePayrollView,
    ClosePayrollView,
    PayrollCommitView,
    PayrollPreviewView,
    DashboardMetricsView,
    CurrentWeekView
)
from .overtime_views import (
    DailyOvertimeAssignmentViewSet,
    OvertimePenaltyViewSet,
    OvertimeProfileViewSet,
    WeeklyOvertimeScheduleViewSet,
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='EmployeeViewSet')
router.register(r'incidence-catalogs', IncidenceCatalogViewSet)
router.register(r'incidence-records', IncidenceRecordViewSet)
router.register(r'loans', LoanViewSet)
router.register(r'extra-hour-banks', ExtraHourBankViewSet)
router.register(r'snapshots', PayrollSnapshotViewSet, basename='payrollsnapshot')
router.register(r'overtime/profiles', OvertimeProfileViewSet, basename='overtime-profile')
router.register(r'overtime/schedules', WeeklyOvertimeScheduleViewSet, basename='overtime-schedule')
router.register(r'overtime/assignments', DailyOvertimeAssignmentViewSet, basename='overtime-assignment')
router.register(r'overtime/penalties', OvertimePenaltyViewSet, basename='overtime-penalty')

urlpatterns = [
    path('', include(router.urls)),
    path('preview/', PayrollPreviewView.as_view(), name='payroll_preview'),
    path('commit/', PayrollCommitView.as_view(), name='payroll_commit'),
    path('calculate/', CalculatePayrollView.as_view(), name='calculate_payroll'),
    path('close/', ClosePayrollView.as_view(), name='close_payroll'),
    path('dashboard/', DashboardMetricsView.as_view(), name='dashboard_metrics'),
    path('current-week/', CurrentWeekView.as_view(), name='current_week'),
]
