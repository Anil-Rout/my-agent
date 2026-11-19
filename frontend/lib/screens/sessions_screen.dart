import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../app_theme.dart';
import '../services/api_service.dart';

class SessionsScreen extends StatefulWidget {
  final ApiService apiService;
  final void Function(String sessionId) onSessionSelected;

  const SessionsScreen({
    super.key,
    required this.apiService,
    required this.onSessionSelected,
  });

  @override
  State<SessionsScreen> createState() => _SessionsScreenState();
}

class _SessionsScreenState extends State<SessionsScreen> {
  List<dynamic> _sessions = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final sessions = await widget.apiService.getSessions();
      setState(() {
        _sessions = sessions;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
        _loading = false;
      });
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'active':
        return AppColors.success;
      case 'running':
        return AppColors.warning;
      case 'error':
        return AppColors.danger;
      default:
        return AppColors.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          decoration: const BoxDecoration(
            color: AppColors.surface,
            border: Border(bottom: BorderSide(color: AppColors.border)),
          ),
          child: Row(
            children: [
              const Text(
                'Sessions',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              const Spacer(),
              Text(
                '${_sessions.length} sessions',
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 12),
              ),
              const SizedBox(width: 12),
              IconButton(
                icon: const Icon(Icons.refresh_rounded, size: 18),
                color: AppColors.textSecondary,
                onPressed: _load,
                tooltip: 'Refresh',
              ),
            ],
          ),
        ),

        Expanded(
          child: _loading
              ? const Center(
                  child: CircularProgressIndicator(
                      color: AppColors.accent, strokeWidth: 2))
              : _error != null
                  ? _buildError()
                  : _sessions.isEmpty
                      ? _buildEmpty()
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _sessions.length,
                          itemBuilder: (context, index) {
                            final session = _sessions[index];
                            return _buildSessionCard(session);
                          },
                        ),
        ),
      ],
    );
  }

  Widget _buildSessionCard(Map<String, dynamic> session) {
    final sessionId = session['session_id'] as String? ?? '';
    final agentName = session['agent_name'] as String? ?? 'Agent';
    final status = session['status'] as String? ?? 'unknown';
    final preview = session['last_message_preview'] as String? ?? '';
    final updatedAt = session['updated_at'] as String?;

    String formattedTime = '';
    if (updatedAt != null) {
      try {
        formattedTime = DateFormat('MMM d, HH:mm')
            .format(DateTime.parse(updatedAt).toLocal());
      } catch (_) {}
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: () => widget.onSessionSelected(sessionId),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                // Status dot
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: _statusColor(status),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 12),

                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            agentName,
                            style: const TextStyle(
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.w600,
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 1),
                            decoration: BoxDecoration(
                              color: AppColors.panel,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              sessionId.length > 20
                                  ? '${sessionId.substring(0, 20)}…'
                                  : sessionId,
                              style: const TextStyle(
                                color: AppColors.textMuted,
                                fontSize: 10,
                                fontFamily: 'Courier New',
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (preview.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          preview.length > 80
                              ? '${preview.substring(0, 80)}…'
                              : preview,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),

                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      formattedTime,
                      style: const TextStyle(
                          color: AppColors.textMuted, fontSize: 11),
                    ),
                    const SizedBox(height: 4),
                    const Icon(Icons.chevron_right_rounded,
                        color: AppColors.textMuted, size: 16),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.error_outline, color: AppColors.danger, size: 36),
          const SizedBox(height: 12),
          Text(_error!,
              style: const TextStyle(color: AppColors.textSecondary)),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _load, child: const Text('Retry')),
        ],
      ),
    );
  }

  Widget _buildEmpty() {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.history_rounded,
              size: 48, color: AppColors.textMuted),
          SizedBox(height: 12),
          Text('No sessions yet',
              style: TextStyle(color: AppColors.textSecondary)),
          SizedBox(height: 6),
          Text('Start a chat to create your first session',
              style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
        ],
      ),
    );
  }
}