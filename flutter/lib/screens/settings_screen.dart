import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../constants/terms.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Map<String, dynamic>? _consentStatus;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadConsentStatus();
  }

  Future<void> _loadConsentStatus() async {
    try {
      final api = context.read<ApiService>();
      _consentStatus = await api.getConsentStatus();
    } catch (_) {
      // API 미지원 서버 호환
    }
    if (mounted) setState(() => _isLoading = false);
  }

  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(url);
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('[SettingsScreen] URL 열기 실패: $e');
    }
  }

  Future<void> _deleteAccount() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('계정 삭제'),
        content: const Text(
          '계정을 삭제하면 모든 개인정보와 데이터가 즉시 삭제되며 복구할 수 없습니다.\n\n'
          'Google Drive에 저장된 파일은 삭제되지 않습니다.\n\n'
          '정말 삭제하시겠습니까?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            child: const Text('계정 삭제'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      final api = context.read<ApiService>();
      await api.deleteAccount();

      // 로컬 데이터 정리
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();

      if (mounted) {
        final auth = context.read<AuthService>();
        await auth.signOut();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('계정이 삭제되었습니다.')),
          );
          Navigator.of(context).popUntil((route) => route.isFirst);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('계정 삭제 실패: $e')),
        );
      }
    }
  }

  Future<void> _withdrawConsent(String type, String label) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('$label 동의 철회'),
        content: Text(
          '$label 동의를 철회하시겠습니까?\n\n'
          '철회 시 관련 기능을 사용할 수 없습니다.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('동의 철회'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      final api = context.read<ApiService>();
      await api.withdrawConsent(type);

      // audio_processing 철회 시 로컬 동의 상태도 초기화
      if (type == 'audio_processing') {
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove('audio_consent_agreed');
      }

      await _loadConsentStatus();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$label 동의가 철회되었습니다.')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('동의 철회 실패: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final user = auth.currentUser;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('설정')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              children: [
                // 사용자 정보
                if (user != null)
                  ListTile(
                    leading: CircleAvatar(
                      backgroundImage: user['avatar_url'] != null
                          ? NetworkImage(user['avatar_url'])
                          : null,
                      child: user['avatar_url'] == null
                          ? Text(user['name']?[0] ?? '?')
                          : null,
                    ),
                    title: Text(user['name'] ?? ''),
                    subtitle: Text(user['email'] ?? ''),
                  ),

                const Divider(),

                // 법적 문서
                Padding(
                  padding: const EdgeInsets.only(left: 16, top: 8, bottom: 4),
                  child: Text('법적 문서',
                      style: theme.textTheme.labelLarge?.copyWith(
                        color: theme.colorScheme.primary,
                      )),
                ),
                ListTile(
                  leading: const Icon(Icons.description_outlined),
                  title: const Text('이용약관'),
                  trailing: const Icon(Icons.open_in_new, size: 18),
                  onTap: () => _openUrl(AppTerms.termsOfServiceUrl),
                ),
                ListTile(
                  leading: const Icon(Icons.privacy_tip_outlined),
                  title: const Text('개인정보 처리방침'),
                  trailing: const Icon(Icons.open_in_new, size: 18),
                  onTap: () => _openUrl(AppTerms.privacyPolicyUrl),
                ),

                const Divider(),

                // 동의 관리
                Padding(
                  padding: const EdgeInsets.only(left: 16, top: 8, bottom: 4),
                  child: Text('동의 관리',
                      style: theme.textTheme.labelLarge?.copyWith(
                        color: theme.colorScheme.primary,
                      )),
                ),
                if (_consentStatus != null)
                  ...(_buildConsentItems(theme))
                else
                  const ListTile(
                    title: Text('동의 정보를 불러올 수 없습니다'),
                  ),

                const Divider(),

                // 계정 관리
                Padding(
                  padding: const EdgeInsets.only(left: 16, top: 8, bottom: 4),
                  child: Text('계정',
                      style: theme.textTheme.labelLarge?.copyWith(
                        color: theme.colorScheme.primary,
                      )),
                ),
                ListTile(
                  leading: const Icon(Icons.logout),
                  title: const Text('로그아웃'),
                  onTap: () {
                    auth.signOut();
                    Navigator.of(context).popUntil((route) => route.isFirst);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.delete_forever, color: Colors.red),
                  title: const Text('계정 삭제',
                      style: TextStyle(color: Colors.red)),
                  subtitle: const Text('모든 데이터가 즉시 삭제됩니다'),
                  onTap: _deleteAccount,
                ),

                const SizedBox(height: 24),

                // 앱 정보
                Center(
                  child: Text(
                    'Proptalk v1.0.0\ncs21.jeon@gmail.com',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
    );
  }

  List<Widget> _buildConsentItems(ThemeData theme) {
    final consents = (_consentStatus?['consents'] as List?) ?? [];
    final consentLabels = {
      'terms': '이용약관',
      'privacy': '개인정보 수집 및 이용',
      'overseas_transfer': '개인정보 국외 이전',
      'audio_processing': '음성 데이터 처리',
    };

    if (consents.isEmpty) {
      return [
        const ListTile(title: Text('동의 이력이 없습니다')),
      ];
    }

    return consents.map<Widget>((c) {
      final type = c['consent_type'] ?? c['type'] ?? '';
      final label = consentLabels[type] ?? type;
      final agreed = c['agreed'] == true && c['withdrawn_at'] == null;

      return ListTile(
        leading: Icon(
          agreed ? Icons.check_circle : Icons.cancel,
          color: agreed ? Colors.green : Colors.grey,
        ),
        title: Text(label),
        subtitle: Text(agreed ? '동의함' : '철회됨'),
        trailing: agreed
            ? TextButton(
                onPressed: () => _withdrawConsent(type, label),
                child: const Text('철회'),
              )
            : null,
      );
    }).toList();
  }
}
