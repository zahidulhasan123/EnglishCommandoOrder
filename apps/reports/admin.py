from datetime import date

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.dateparse import parse_date

from apps.reports.services.report_service import ReportService


class ReportsAdminView(admin.ModelAdmin):
	pass


def _to_int(value: str, default: int) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def report_index(request):
	context = {
		**admin.site.each_context(request),
		"title": "Reports",
	}
	return TemplateResponse(request, "admin/reports/index.html", context)


def daily_report_view(request):
	target_date = parse_date(request.GET.get("date", "")) or date.today()
	context = {
		**admin.site.each_context(request),
		"title": "Daily Report",
		"report_date": target_date,
		"data": ReportService.for_date(target_date),
	}
	return TemplateResponse(request, "admin/reports/daily.html", context)


def weekly_report_view(request):
	mode = request.GET.get("mode", "current")
	start = parse_date(request.GET.get("start", ""))
	end = parse_date(request.GET.get("end", ""))
	if start and end:
		data = ReportService.weekly(start_date=start, end_date=end)
	else:
		data = ReportService.weekly(current_week=(mode != "previous"))
	context = {
		**admin.site.each_context(request),
		"title": "Weekly Report",
		"data": data,
	}
	return TemplateResponse(request, "admin/reports/weekly.html", context)


def monthly_report_view(request):
	today = date.today()
	year = _to_int(request.GET.get("year"), today.year)
	month = _to_int(request.GET.get("month"), today.month)
	context = {
		**admin.site.each_context(request),
		"title": "Monthly Report",
		"year": year,
		"month": month,
		"data": ReportService.monthly(year=year, month=month),
	}
	return TemplateResponse(request, "admin/reports/monthly.html", context)


def custom_range_report_view(request):
	start = parse_date(request.GET.get("start", ""))
	end = parse_date(request.GET.get("end", ""))
	data = ReportService.custom_range(start, end) if start and end else None
	context = {
		**admin.site.each_context(request),
		"title": "Custom Range Report",
		"start": start,
		"end": end,
		"data": data,
	}
	return TemplateResponse(request, "admin/reports/custom.html", context)


def get_report_urls():
	return [
		path("reports/", admin.site.admin_view(report_index), name="reports-index"),
		path("reports/daily/", admin.site.admin_view(daily_report_view), name="reports-daily"),
		path("reports/weekly/", admin.site.admin_view(weekly_report_view), name="reports-weekly"),
		path("reports/monthly/", admin.site.admin_view(monthly_report_view), name="reports-monthly"),
		path("reports/custom/", admin.site.admin_view(custom_range_report_view), name="reports-custom"),
	]
