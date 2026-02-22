import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../../../../core/theme/app_colors.dart';

class MessageBubble extends StatelessWidget {
  final String message;
  final bool isUser;
  final bool isError;

  const MessageBubble({
    super.key,
    required this.message,
    required this.isUser,
    this.isError = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    Color textColor;
    BoxDecoration decoration;

    if (isError) {
      textColor = colorScheme.onErrorContainer;
      decoration = BoxDecoration(
        color: colorScheme.errorContainer,
        borderRadius: _bubbleRadius(isUser),
      );
    } else if (isUser) {
      textColor = Colors.white;
      decoration = BoxDecoration(
        color: AppColors.indigo,
        borderRadius: _bubbleRadius(isUser),
        boxShadow: const [
          BoxShadow(
            color: AppColors.indigoGlow,
            blurRadius: 12,
            offset: Offset(0, 4),
          ),
        ],
      );
    } else {
      textColor = colorScheme.onSurface;
      decoration = BoxDecoration(
        gradient: isDark
            ? const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppColors.white05, Colors.transparent],
              )
            : null,
        color: isDark ? null : colorScheme.surfaceContainerHighest,
        borderRadius: _bubbleRadius(isUser),
        border: isDark
            ? Border.all(color: colorScheme.outlineVariant)
            : null,
      );
    }

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.8,
        ),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: decoration,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (isError)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: Icon(
                  Icons.error_outline,
                  color: textColor,
                  size: 20,
                ),
              ),
            Flexible(
              child: MarkdownBody(
                data: message,
                styleSheet: MarkdownStyleSheet(
                  p: TextStyle(color: textColor),
                  code: TextStyle(
                    backgroundColor: isUser
                        ? Colors.white.withValues(alpha: 0.15)
                        : colorScheme.surfaceContainerHigh,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  BorderRadius _bubbleRadius(bool isUser) {
    return BorderRadius.only(
      topLeft: const Radius.circular(16),
      topRight: const Radius.circular(16),
      bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(4),
      bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(16),
    );
  }
}
