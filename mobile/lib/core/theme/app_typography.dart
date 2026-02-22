import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Design tokens: typography using Space Grotesk for headings and Inter for body.
abstract final class AppTypography {
  /// Full [TextTheme] built from Google Fonts.
  ///
  /// Headings → Space Grotesk (geometric, matches landing hero text).
  /// Body / labels → Inter (clean, highly readable).
  static TextTheme textTheme(Brightness brightness) {
    final color = brightness == Brightness.dark ? Colors.white : Colors.black;

    final headingStyle = GoogleFonts.spaceGrotesk(color: color);
    final bodyStyle = GoogleFonts.inter(color: color);

    return TextTheme(
      // ── Display ──
      displayLarge: headingStyle.copyWith(
        fontSize: 57,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.25,
      ),
      displayMedium: headingStyle.copyWith(
        fontSize: 45,
        fontWeight: FontWeight.w700,
      ),
      displaySmall: headingStyle.copyWith(
        fontSize: 36,
        fontWeight: FontWeight.w700,
      ),
      // ── Headline ──
      headlineLarge: headingStyle.copyWith(
        fontSize: 32,
        fontWeight: FontWeight.w700,
      ),
      headlineMedium: headingStyle.copyWith(
        fontSize: 28,
        fontWeight: FontWeight.w600,
      ),
      headlineSmall: headingStyle.copyWith(
        fontSize: 24,
        fontWeight: FontWeight.w600,
      ),
      // ── Title ──
      titleLarge: headingStyle.copyWith(
        fontSize: 22,
        fontWeight: FontWeight.w600,
      ),
      titleMedium: bodyStyle.copyWith(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.15,
      ),
      titleSmall: bodyStyle.copyWith(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.1,
      ),
      // ── Body ──
      bodyLarge: bodyStyle.copyWith(
        fontSize: 16,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.15,
      ),
      bodyMedium: bodyStyle.copyWith(
        fontSize: 14,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.25,
      ),
      bodySmall: bodyStyle.copyWith(
        fontSize: 12,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.4,
      ),
      // ── Label ──
      labelLarge: bodyStyle.copyWith(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.1,
      ),
      labelMedium: bodyStyle.copyWith(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      ),
      labelSmall: bodyStyle.copyWith(
        fontSize: 11,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      ),
    );
  }
}
