import 'package:flutter/material.dart';

/// 프롭넷 공통 푸터 위젯
class PropnetFooter extends StatelessWidget {
  const PropnetFooter({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Image.asset(
                'assets/images/Propnet_icon_transparent_full_size.png',
                height: 20,
                width: 20,
              ),
              const SizedBox(width: 6),
              Text(
                '프롭넷 | 부동산 종합 서비스',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '\u00a9 2026 Propnet',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.outline,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}
