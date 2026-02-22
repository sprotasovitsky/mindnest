import 'package:flutter/material.dart';

/// Design tokens: color palette derived from the MindNest landing page.
///
/// Dark palette comes directly from the landing (indigo / deep navy).
/// Light palette is an adapted inversion that keeps the same accent hues.
abstract final class AppColors {
  // ── Brand / Accent ─────────────────────────────────────────────────
  static const indigo = Color(0xFF6366F1);
  static const indigoLight = Color(0xFF818CF8);
  static const indigoDark = Color(0xFF4F46E5);

  // ── Dark theme surfaces (from landing) ─────────────────────────────
  static const darkSurface = Color(0xFF0B1026);
  static const darkSurfaceContainer = Color(0xFF111338);
  static const darkSurfaceContainerHigh = Color(0xFF161845);
  static const darkSurfaceContainerHighest = Color(0xFF1A1B4B);

  // ── Light theme surfaces ───────────────────────────────────────────
  static const lightSurface = Color(0xFFF8F9FC);
  static const lightSurfaceContainer = Color(0xFFF0F1F8);
  static const lightSurfaceContainerHigh = Color(0xFFE8E9F4);
  static const lightSurfaceContainerHighest = Color(0xFFE5E5EF);

  // ── White opacity scale (dark theme foregrounds) ───────────────────
  static const white90 = Color(0xE6FFFFFF);
  static const white70 = Color(0xB3FFFFFF);
  static const white50 = Color(0x80FFFFFF);
  static const white20 = Color(0x33FFFFFF);
  static const white10 = Color(0x1AFFFFFF);
  static const white05 = Color(0x0DFFFFFF);

  // ── Black opacity scale (light theme foregrounds) ──────────────────
  static const black90 = Color(0xE6000000);
  static const black70 = Color(0xB3000000);
  static const black50 = Color(0x80000000);
  static const black20 = Color(0x33000000);
  static const black10 = Color(0x1A000000);
  static const black05 = Color(0x0D000000);

  // ── Semantic colors ────────────────────────────────────────────────
  static const success = Color(0xFF22C55E);
  static const successContainer = Color(0xFF052E16);
  static const successContainerLight = Color(0xFFDCFCE7);
  static const error = Color(0xFFEF4444);
  static const errorContainer = Color(0xFF450A0A);
  static const errorContainerLight = Color(0xFFFEE2E2);
  static const warning = Color(0xFFF59E0B);

  // ── Glow shadow for indigo elements ────────────────────────────────
  static const indigoGlow = Color(0x406366F1); // 25% opacity
  static const indigoGlowStrong = Color(0x666366F1); // 40% opacity

  // ── Light theme primary container ──────────────────────────────────
  static const primaryContainerLight = Color(0xFFEEF2FF);
  static const onPrimaryContainerLight = Color(0xFF3730A3);
}
