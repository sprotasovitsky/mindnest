package com.mindnest.agent.tools;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.TemporalAdjusters;
import java.util.HashMap;
import java.util.Map;

/**
 * Tools for working with dates and times.
 * These are programmatic (no LLM needed) to ensure accuracy.
 */
@Component
@Slf4j
public class TimeTools {

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");
    private static final DateTimeFormatter DISPLAY_FORMATTER = DateTimeFormatter.ofPattern("EEEE, MMMM d, yyyy");

    /**
     * Get current date
     */
    public LocalDate getCurrentDate() {
        return LocalDate.now();
    }

    /**
     * Get current date as formatted string
     */
    public String getCurrentDateFormatted() {
        return LocalDate.now().format(DISPLAY_FORMATTER);
    }

    /**
     * Get current date and time info
     */
    public Map<String, Object> getCurrentDateTimeInfo() {
        LocalDateTime now = LocalDateTime.now();
        LocalDate today = now.toLocalDate();

        Map<String, Object> info = new HashMap<>();
        info.put("date", today.format(DATE_FORMATTER));
        info.put("dayOfWeek", today.getDayOfWeek().toString());
        info.put("formatted", today.format(DISPLAY_FORMATTER));
        info.put("isWeekend", today.getDayOfWeek() == DayOfWeek.SATURDAY ||
                today.getDayOfWeek() == DayOfWeek.SUNDAY);
        return info;
    }

    /**
     * Parse date from various formats
     */
    public LocalDate parseDate(String dateStr) {
        if (dateStr == null || dateStr.isBlank()) {
            return null;
        }

        String normalized = dateStr.toLowerCase().trim();
        LocalDate today = LocalDate.now();

        // Handle relative dates
        return switch (normalized) {
            case "today", "сегодня" -> today;
            case "tomorrow", "завтра" -> today.plusDays(1);
            case "yesterday", "вчера" -> today.minusDays(1);
            case "next week", "следующая неделя" -> today.plusWeeks(1);
            case "next month", "следующий месяц" -> today.plusMonths(1);
            case "monday", "понедельник" -> today.with(TemporalAdjusters.next(DayOfWeek.MONDAY));
            case "tuesday", "вторник" -> today.with(TemporalAdjusters.next(DayOfWeek.TUESDAY));
            case "wednesday", "среда" -> today.with(TemporalAdjusters.next(DayOfWeek.WEDNESDAY));
            case "thursday", "четверг" -> today.with(TemporalAdjusters.next(DayOfWeek.THURSDAY));
            case "friday", "пятница" -> today.with(TemporalAdjusters.next(DayOfWeek.FRIDAY));
            case "saturday", "суббота" -> today.with(TemporalAdjusters.next(DayOfWeek.SATURDAY));
            case "sunday", "воскресенье" -> today.with(TemporalAdjusters.next(DayOfWeek.SUNDAY));
            case "end of week", "конец недели" -> today.with(TemporalAdjusters.next(DayOfWeek.FRIDAY));
            case "end of month", "конец месяца" -> today.with(TemporalAdjusters.lastDayOfMonth());
            default -> tryParseExact(dateStr);
        };
    }

    private LocalDate tryParseExact(String dateStr) {
        // Try various date formats
        String[] formats = {
                "yyyy-MM-dd",
                "dd.MM.yyyy",
                "dd/MM/yyyy",
                "MM/dd/yyyy",
                "d MMMM yyyy",
                "d MMMM",
                "MMMM d"
        };

        for (String format : formats) {
            try {
                DateTimeFormatter formatter = DateTimeFormatter.ofPattern(format);
                return LocalDate.parse(dateStr, formatter);
            } catch (Exception ignored) {
            }
        }

        // Try parsing just day and month, assume current year
        try {
            String[] parts = dateStr.split("[./\\-]");
            if (parts.length == 2) {
                int day = Integer.parseInt(parts[0]);
                int month = Integer.parseInt(parts[1]);
                return LocalDate.of(LocalDate.now().getYear(), month, day);
            }
        } catch (Exception ignored) {
        }

        log.warn("Could not parse date: {}", dateStr);
        return null;
    }

    /**
     * Format date for display
     */
    public String formatDate(LocalDate date) {
        if (date == null) return "no date";

        LocalDate today = LocalDate.now();
        if (date.equals(today)) {
            return "today";
        } else if (date.equals(today.plusDays(1))) {
            return "tomorrow";
        } else if (date.equals(today.minusDays(1))) {
            return "yesterday";
        } else if (date.isAfter(today) && date.isBefore(today.plusWeeks(1))) {
            return date.getDayOfWeek().toString().toLowerCase();
        } else {
            return date.format(DISPLAY_FORMATTER);
        }
    }

    /**
     * Check if date is in the past
     */
    public boolean isOverdue(LocalDate deadline) {
        return deadline != null && deadline.isBefore(LocalDate.now());
    }

    /**
     * Check if date is today
     */
    public boolean isToday(LocalDate date) {
        return date != null && date.equals(LocalDate.now());
    }

    /**
     * Get days until deadline
     */
    public long daysUntil(LocalDate deadline) {
        if (deadline == null) return Long.MAX_VALUE;
        return java.time.temporal.ChronoUnit.DAYS.between(LocalDate.now(), deadline);
    }
}
