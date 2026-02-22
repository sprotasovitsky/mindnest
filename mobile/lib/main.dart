import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_web_plugins/url_strategy.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'shared/widgets/knowledge_graph_background.dart';

void main() {
  // Use path-based URL strategy for web (e.g., /verify-email instead of /#/verify-email)
  // This is required for deep links to work properly
  usePathUrlStrategy();

  runApp(
    const ProviderScope(
      child: MindNestApp(),
    ),
  );
}

class MindNestApp extends ConsumerWidget {
  const MindNestApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'MindNest',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
      builder: (context, child) => Stack(
        children: [
          const KnowledgeGraphBackground(),
          child!,
        ],
      ),
    );
  }
}
