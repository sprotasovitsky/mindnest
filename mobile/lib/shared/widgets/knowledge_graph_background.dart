import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

/// Animated knowledge graph background that renders floating nodes and
/// pulsing connection lines. Designed to sit behind all screens via
/// [MaterialApp.router]'s `builder`.
///
/// The widget paints the surface color itself so that scaffolds can use
/// [Colors.transparent] without losing their solid background.
class KnowledgeGraphBackground extends StatefulWidget {
  const KnowledgeGraphBackground({super.key});

  @override
  State<KnowledgeGraphBackground> createState() =>
      _KnowledgeGraphBackgroundState();
}

class _KnowledgeGraphBackgroundState extends State<KnowledgeGraphBackground>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      // Arbitrary long duration — we use elapsed time, not value.
      duration: const Duration(seconds: 120),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return RepaintBoundary(
      child: CustomPaint(
        painter: _GraphPainter(
          repaint: _controller,
          isDark: isDark,
        ),
        size: Size.infinite,
      ),
    );
  }
}

// ─── Data ──────────────────────────────────────────────────────────────────

class _Node {
  const _Node(this.xPct, this.yPct, this.radius, this.opacity,
      this.floatPx, this.cycleSec, this.delaySec);

  final double xPct;
  final double yPct;
  final double radius;
  final double opacity;
  final double floatPx;
  final double cycleSec;
  final double delaySec;
}

class _Edge {
  const _Edge(this.fromIdx, this.toIdx, this.opacity, this.peakOpacity,
      this.cycleSec, this.delaySec);

  final int fromIdx;
  final int toIdx;
  final double opacity;
  final double peakOpacity;
  final double cycleSec;
  final double delaySec;
}

// 18 nodes — positions as percentage of screen width/height
const _nodes = <_Node>[
  _Node(0.08, 0.05, 2.0, 0.07, 5, 10, 0),
  _Node(0.25, 0.08, 1.8, 0.06, 4, 9, 1.2),
  _Node(0.50, 0.04, 2.5, 0.08, 6, 11, 2.5),
  _Node(0.72, 0.07, 1.5, 0.05, 4, 8, 0.8),
  _Node(0.90, 0.10, 2.2, 0.09, 5, 12, 3.0),
  _Node(0.12, 0.25, 2.0, 0.06, 5, 10, 1.5),
  _Node(0.35, 0.22, 2.3, 0.08, 6, 11, 0.3),
  _Node(0.60, 0.20, 1.8, 0.07, 4, 9, 2.0),
  _Node(0.85, 0.28, 2.0, 0.05, 5, 10, 1.0),
  _Node(0.05, 0.45, 1.5, 0.06, 4, 8, 2.8),
  _Node(0.30, 0.42, 2.5, 0.09, 6, 12, 0.5),
  _Node(0.55, 0.48, 2.0, 0.07, 5, 10, 1.8),
  _Node(0.78, 0.44, 1.8, 0.06, 4, 9, 3.2),
  _Node(0.15, 0.65, 2.2, 0.08, 5, 11, 0.7),
  _Node(0.42, 0.68, 1.5, 0.05, 4, 8, 2.2),
  _Node(0.65, 0.62, 2.0, 0.07, 6, 10, 1.3),
  _Node(0.88, 0.70, 2.3, 0.09, 5, 12, 0.0),
  _Node(0.50, 0.88, 2.0, 0.06, 5, 10, 2.5),
];

// 20 connections between nodes
const _edges = <_Edge>[
  _Edge(0, 1, 0.04, 0.12, 6, 0),
  _Edge(1, 2, 0.05, 0.10, 6, 1.0),
  _Edge(2, 3, 0.04, 0.11, 6, 2.0),
  _Edge(3, 4, 0.06, 0.12, 6, 0.5),
  _Edge(5, 6, 0.05, 0.10, 6, 1.5),
  _Edge(6, 7, 0.04, 0.11, 6, 2.5),
  _Edge(7, 8, 0.05, 0.12, 6, 0.3),
  _Edge(9, 10, 0.06, 0.10, 6, 1.8),
  _Edge(10, 11, 0.04, 0.11, 6, 3.0),
  _Edge(11, 12, 0.05, 0.12, 6, 0.8),
  _Edge(13, 14, 0.06, 0.10, 6, 2.2),
  _Edge(14, 15, 0.04, 0.11, 6, 1.2),
  _Edge(15, 16, 0.05, 0.12, 6, 0.0),
  _Edge(0, 5, 0.04, 0.10, 6, 2.8),
  _Edge(1, 6, 0.05, 0.11, 6, 1.0),
  _Edge(6, 10, 0.04, 0.12, 6, 0.5),
  _Edge(10, 13, 0.06, 0.10, 6, 3.5),
  _Edge(7, 11, 0.05, 0.11, 6, 1.5),
  _Edge(11, 15, 0.04, 0.12, 6, 2.0),
  _Edge(14, 17, 0.05, 0.10, 6, 0.7),
];

// ─── Painter ───────────────────────────────────────────────────────────────

class _GraphPainter extends CustomPainter {
  _GraphPainter({required Listenable repaint, required this.isDark})
      : super(repaint: repaint);

  final bool isDark;

  // Gradient center color — deep indigo from landing (#1A1B4B at 40% alpha).
  static const _gradientCenter = Color(0x661A1B4B);

  @override
  void paint(Canvas canvas, Size size) {
    // 1. Solid surface fill
    final surfaceColor =
        isDark ? AppColors.darkSurface : AppColors.lightSurface;
    canvas.drawRect(Offset.zero & size, Paint()..color = surfaceColor);

    // 2. Radial gradient overlay (dark only)
    if (isDark) {
      const gradient = RadialGradient(
        center: Alignment.center,
        radius: 1.0,
        colors: [_gradientCenter, Colors.transparent],
      );
      canvas.drawRect(
        Offset.zero & size,
        Paint()..shader = gradient.createShader(Offset.zero & size),
      );
    }

    final elapsed =
        (WidgetsBinding.instance.currentFrameTimeStamp.inMicroseconds) /
            1e6; // seconds

    // Pre-compute animated node positions
    final positions = List<Offset>.generate(_nodes.length, (i) {
      final n = _nodes[i];
      final t = (elapsed - n.delaySec) / n.cycleSec;
      final dx = math.sin(t * 2 * math.pi) * n.floatPx;
      final dy = math.cos(t * 2 * math.pi * 0.7) * n.floatPx;
      return Offset(n.xPct * size.width + dx, n.yPct * size.height + dy);
    });

    // Determine base color + opacity multiplier for theme
    final baseColor = isDark ? Colors.white : Colors.black;
    final opacityScale = isDark ? 1.0 : 0.4;

    // 3. Draw edges
    for (final e in _edges) {
      final t = (elapsed - e.delaySec) / e.cycleSec;
      final pulse = (math.sin(t * 2 * math.pi) + 1) / 2; // 0..1
      final alpha = e.opacity + (e.peakOpacity - e.opacity) * pulse;
      final paint = Paint()
        ..color = baseColor.withValues(alpha: alpha * opacityScale)
        ..strokeWidth = 0.5
        ..style = PaintingStyle.stroke;
      canvas.drawLine(positions[e.fromIdx], positions[e.toIdx], paint);
    }

    // 4. Draw nodes
    for (var i = 0; i < _nodes.length; i++) {
      final n = _nodes[i];
      final paint = Paint()
        ..color = baseColor.withValues(alpha: n.opacity * opacityScale);
      canvas.drawCircle(positions[i], n.radius, paint);
    }
  }

  @override
  bool shouldRepaint(_GraphPainter oldDelegate) => isDark != oldDelegate.isDark;
}
