package com.mindnest.agent.tools;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.DayOfWeek;
import java.time.LocalDate;

import static org.junit.jupiter.api.Assertions.*;

class TimeToolsTest {

    private TimeTools timeTools;

    @BeforeEach
    void setUp() {
        timeTools = new TimeTools();
    }

    @Test
    void getCurrentDate_returnsToday() {
        LocalDate result = timeTools.getCurrentDate();
        assertEquals(LocalDate.now(), result);
    }

    @Test
    void parseDate_today_returnsCurrentDate() {
        assertEquals(LocalDate.now(), timeTools.parseDate("today"));
        assertEquals(LocalDate.now(), timeTools.parseDate("сегодня"));
    }

    @Test
    void parseDate_tomorrow_returnsNextDay() {
        assertEquals(LocalDate.now().plusDays(1), timeTools.parseDate("tomorrow"));
        assertEquals(LocalDate.now().plusDays(1), timeTools.parseDate("завтра"));
    }

    @Test
    void parseDate_dayOfWeek_returnsNextOccurrence() {
        LocalDate monday = timeTools.parseDate("monday");
        assertNotNull(monday);
        assertEquals(DayOfWeek.MONDAY, monday.getDayOfWeek());
        assertTrue(monday.isAfter(LocalDate.now()) || monday.isEqual(LocalDate.now()));
    }

    @Test
    void parseDate_isoFormat_parsesCorrectly() {
        LocalDate result = timeTools.parseDate("2025-12-25");
        assertEquals(LocalDate.of(2025, 12, 25), result);
    }

    @Test
    void parseDate_monthDayFormat_usesCurrentOrNextYear() {
        LocalDate result = timeTools.parseDate("December 25");
        assertNotNull(result);
        assertEquals(12, result.getMonthValue());
        assertEquals(25, result.getDayOfMonth());
        // Should be this year or next year
        assertTrue(result.getYear() >= LocalDate.now().getYear());
    }

    @Test
    void parseDate_nullOrEmpty_returnsNull() {
        assertNull(timeTools.parseDate(null));
        assertNull(timeTools.parseDate(""));
        assertNull(timeTools.parseDate("   "));
    }

    @Test
    void formatDate_today_returnsToday() {
        assertEquals("today", timeTools.formatDate(LocalDate.now()));
    }

    @Test
    void formatDate_tomorrow_returnsTomorrow() {
        assertEquals("tomorrow", timeTools.formatDate(LocalDate.now().plusDays(1)));
    }

    @Test
    void isOverdue_pastDate_returnsTrue() {
        assertTrue(timeTools.isOverdue(LocalDate.now().minusDays(1)));
    }

    @Test
    void isOverdue_futureDate_returnsFalse() {
        assertFalse(timeTools.isOverdue(LocalDate.now().plusDays(1)));
    }

    @Test
    void isOverdue_null_returnsFalse() {
        assertFalse(timeTools.isOverdue(null));
    }

    @Test
    void isToday_currentDate_returnsTrue() {
        assertTrue(timeTools.isToday(LocalDate.now()));
    }

    @Test
    void isToday_differentDate_returnsFalse() {
        assertFalse(timeTools.isToday(LocalDate.now().plusDays(1)));
    }

    @Test
    void daysUntil_futureDate_returnsPositive() {
        long days = timeTools.daysUntil(LocalDate.now().plusDays(5));
        assertEquals(5, days);
    }

    @Test
    void daysUntil_pastDate_returnsNegative() {
        long days = timeTools.daysUntil(LocalDate.now().minusDays(3));
        assertEquals(-3, days);
    }

    @Test
    void getCurrentDateTimeInfo_containsExpectedFields() {
        var info = timeTools.getCurrentDateTimeInfo();
        assertNotNull(info.get("date"));
        assertNotNull(info.get("dayOfWeek"));
        assertNotNull(info.get("formatted"));
        assertNotNull(info.get("isWeekend"));
    }
}
