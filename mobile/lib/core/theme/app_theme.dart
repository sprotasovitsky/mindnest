import 'package:flutter/material.dart';

import 'app_colors.dart';
import 'app_spacing.dart';
import 'app_typography.dart';

class AppTheme {
  AppTheme._();

  // ─── Dark Theme ─────────────────────────────────────────────────────
  static final dark = _build(Brightness.dark);

  // ─── Light Theme ────────────────────────────────────────────────────
  static final light = _build(Brightness.light);

  static ThemeData _build(Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    final colorScheme = isDark ? _darkScheme : _lightScheme;
    final textTheme = AppTypography.textTheme(brightness);

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: colorScheme,
      textTheme: textTheme,
      scaffoldBackgroundColor: colorScheme.surface,

      // ── AppBar ───────────────────────────────────────────────────
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 0,
        backgroundColor: colorScheme.surface,
        foregroundColor: colorScheme.onSurface,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: textTheme.titleLarge?.copyWith(
          color: colorScheme.onSurface,
          fontSize: 20,
        ),
      ),

      // ── Card ─────────────────────────────────────────────────────
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.borderRadiusXl,
          side: BorderSide(color: colorScheme.outlineVariant),
        ),
        color: colorScheme.surfaceContainer,
        surfaceTintColor: Colors.transparent,
      ),

      // ── FilledButton (pill) ──────────────────────────────────────
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.indigo,
          foregroundColor: Colors.white,
          minimumSize: const Size(0, 52),
          shape: RoundedRectangleBorder(
            borderRadius: AppSpacing.borderRadiusPill,
          ),
          textStyle: textTheme.labelLarge,
        ),
      ),

      // ── ElevatedButton ───────────────────────────────────────────
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(0, 52),
          shape: RoundedRectangleBorder(
            borderRadius: AppSpacing.borderRadiusPill,
          ),
          textStyle: textTheme.labelLarge,
        ),
      ),

      // ── OutlinedButton (pill) ────────────────────────────────────
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: colorScheme.onSurface,
          minimumSize: const Size(0, 52),
          side: BorderSide(color: colorScheme.outline),
          shape: RoundedRectangleBorder(
            borderRadius: AppSpacing.borderRadiusPill,
          ),
          textStyle: textTheme.labelLarge,
        ),
      ),

      // ── TextButton ──────────────────────────────────────────────
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.indigo,
          textStyle: textTheme.labelLarge,
        ),
      ),

      // ── IconButton ──────────────────────────────────────────────
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(
          foregroundColor: colorScheme.onSurface,
        ),
      ),

      // ── Input / TextField (filled, radius 12) ───────────────────
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: colorScheme.surfaceContainer,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md,
        ),
        border: OutlineInputBorder(
          borderRadius: AppSpacing.borderRadiusMd,
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: AppSpacing.borderRadiusMd,
          borderSide: BorderSide(color: colorScheme.outlineVariant),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: AppSpacing.borderRadiusMd,
          borderSide: const BorderSide(color: AppColors.indigo, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: AppSpacing.borderRadiusMd,
          borderSide: BorderSide(color: colorScheme.error),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: AppSpacing.borderRadiusMd,
          borderSide: BorderSide(color: colorScheme.error, width: 2),
        ),
        labelStyle: TextStyle(color: colorScheme.onSurfaceVariant),
        hintStyle: TextStyle(color: colorScheme.onSurfaceVariant),
      ),

      // ── FAB (indigo + glow in dark) ─────────────────────────────
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: AppColors.indigo,
        foregroundColor: Colors.white,
        elevation: isDark ? 0 : 4,
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.borderRadiusLg,
        ),
      ),

      // ── Dialog ──────────────────────────────────────────────────
      dialogTheme: DialogThemeData(
        backgroundColor: isDark
            ? AppColors.darkSurfaceContainer
            : colorScheme.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.borderRadiusXl,
        ),
        titleTextStyle: textTheme.titleLarge?.copyWith(
          color: colorScheme.onSurface,
        ),
      ),

      // ── BottomSheet ─────────────────────────────────────────────
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: isDark
            ? AppColors.darkSurfaceContainer
            : colorScheme.surface,
        surfaceTintColor: Colors.transparent,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(AppSpacing.radiusXl),
          ),
        ),
        showDragHandle: true,
        dragHandleColor: colorScheme.onSurfaceVariant.withValues(alpha: 0.4),
      ),

      // ── Chip ────────────────────────────────────────────────────
      chipTheme: ChipThemeData(
        backgroundColor: colorScheme.surfaceContainerHighest,
        side: BorderSide.none,
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.borderRadiusPill,
        ),
        labelStyle: textTheme.labelMedium?.copyWith(
          color: colorScheme.onSurfaceVariant,
        ),
      ),

      // ── SnackBar ────────────────────────────────────────────────
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.borderRadiusMd,
        ),
        backgroundColor: isDark
            ? AppColors.darkSurfaceContainerHighest
            : const Color(0xFF323232),
        contentTextStyle: const TextStyle(color: Colors.white),
      ),

      // ── ListTile ────────────────────────────────────────────────
      listTileTheme: ListTileThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.borderRadiusMd,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
      ),

      // ── Divider ─────────────────────────────────────────────────
      dividerTheme: DividerThemeData(
        color: colorScheme.outlineVariant,
        thickness: 1,
      ),

      // ── ProgressIndicator ───────────────────────────────────────
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: AppColors.indigo,
        linearTrackColor: colorScheme.surfaceContainerHighest,
      ),

      // ── TextSelection ───────────────────────────────────────────
      textSelectionTheme: TextSelectionThemeData(
        cursorColor: AppColors.indigo,
        selectionColor: AppColors.indigo.withValues(alpha: 0.3),
        selectionHandleColor: AppColors.indigo,
      ),
    );
  }

  // ─── Dark ColorScheme ───────────────────────────────────────────────
  static const _darkScheme = ColorScheme(
    brightness: Brightness.dark,
    primary: AppColors.indigo,
    onPrimary: Colors.white,
    primaryContainer: AppColors.darkSurfaceContainerHighest,
    onPrimaryContainer: AppColors.indigoLight,
    secondary: AppColors.indigoLight,
    onSecondary: Colors.black,
    secondaryContainer: AppColors.darkSurfaceContainerHighest,
    onSecondaryContainer: AppColors.indigoLight,
    surface: AppColors.darkSurface,
    onSurface: AppColors.white90,
    onSurfaceVariant: AppColors.white70,
    surfaceContainer: AppColors.darkSurfaceContainer,
    surfaceContainerHigh: AppColors.darkSurfaceContainerHigh,
    surfaceContainerHighest: AppColors.darkSurfaceContainerHighest,
    error: AppColors.error,
    onError: Colors.white,
    errorContainer: AppColors.errorContainer,
    onErrorContainer: Color(0xFFFCA5A5),
    outline: AppColors.white20,
    outlineVariant: AppColors.white10,
  );

  // ─── Light ColorScheme ──────────────────────────────────────────────
  static const _lightScheme = ColorScheme(
    brightness: Brightness.light,
    primary: AppColors.indigo,
    onPrimary: Colors.white,
    primaryContainer: AppColors.primaryContainerLight,
    onPrimaryContainer: AppColors.onPrimaryContainerLight,
    secondary: AppColors.indigoDark,
    onSecondary: Colors.white,
    secondaryContainer: AppColors.primaryContainerLight,
    onSecondaryContainer: AppColors.onPrimaryContainerLight,
    surface: AppColors.lightSurface,
    onSurface: AppColors.black90,
    onSurfaceVariant: AppColors.black70,
    surfaceContainer: AppColors.lightSurfaceContainer,
    surfaceContainerHigh: AppColors.lightSurfaceContainerHigh,
    surfaceContainerHighest: AppColors.lightSurfaceContainerHighest,
    error: AppColors.error,
    onError: Colors.white,
    errorContainer: AppColors.errorContainerLight,
    onErrorContainer: Color(0xFF991B1B),
    outline: AppColors.black20,
    outlineVariant: AppColors.black10,
  );
}
