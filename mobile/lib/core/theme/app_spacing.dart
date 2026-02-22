import 'package:flutter/material.dart';

/// Design tokens: spacing scale and border radii.
abstract final class AppSpacing {
  // ── Spacing scale ──────────────────────────────────────────────────
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 20;
  static const double xxl = 24;
  static const double xxxl = 32;
  static const double huge = 48;

  // ── Border radii ───────────────────────────────────────────────────
  static const double radiusSm = 8;
  static const double radiusMd = 12;
  static const double radiusLg = 16;
  static const double radiusXl = 20;
  static const double radiusXxl = 24;
  static const double radiusPill = 100;

  // ── Pre-built BorderRadius ─────────────────────────────────────────
  static final borderRadiusSm = BorderRadius.circular(radiusSm);
  static final borderRadiusMd = BorderRadius.circular(radiusMd);
  static final borderRadiusLg = BorderRadius.circular(radiusLg);
  static final borderRadiusXl = BorderRadius.circular(radiusXl);
  static final borderRadiusXxl = BorderRadius.circular(radiusXxl);
  static final borderRadiusPill = BorderRadius.circular(radiusPill);
}
