import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/api_service.dart';

class ActivityScreen extends StatefulWidget {
  final ApiService apiService;
  const ActivityScreen({super.key, required this.apiService});

  @override
  State<ActivityScreen> createState() => _ActivityScreenState();
}

class _ActivityScreenState extends State<ActivityScreen> {
  List<dynamic> _activity = [];
  Map<String, dynamic> _summary = {};
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
      final results = await Future.wait([
        widget.apiService.getActivity(),
        widget.apiService.getActivitySummary(),
      ]);
      setState(() {
        _activity = results[0] as List;
        _summary = results[1] as Map<String, dynamic>;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
        _loading = false;
      });
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
                'Activity Log',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              const Spacer(),
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
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (_summary.isNotEmpty) _buildSummaryCards(),
                          const SizedBox(height: 16),
                          _buildActivityList(),
                        ],
                      ),
                    ),
        ),
      ],
    );
  }

  Widget _buildSummaryCards() {
    final total = _summary['total_actions'] ?? 0;
    final success = _summary['successful_actions'] ?? 0;
    final failed = _summary['failed_actions'] ?? 0;

    return Row(
      children: [
        _StatCard(label: 'Total Actions', value: '$total',
            color: AppColors.accent),
        const SizedBox(width: 10),
        _StatCard(label: 'Successful', value: '$success',
            color: AppColors.success),
        const SizedBox(width: 10),
        _StatCard(label: 'Failed', value: '$failed',
            color: failed > 0 ? AppColors.danger : AppColors.textMuted),
      ],
    );
  }

  Widget _buildActivityList() {
    if (_activity.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(40),
          child: Column(
            children: [
              Icon(Icons.receipt_long_rounded,
                  size: 48, color: AppColors.textMuted),
              SizedBox(height: 12),
              Text('No tool activity yet',
                  style: TextStyle(color: AppColors.textSecondary)),
              SizedBox(height: 6),
              Text('Tool calls will appear here as you chat',
                  style: TextStyle(
                      color: AppColors.textMuted, fontSize: 12)),
            ],
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Recent tool calls',
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        ..._activity.map((item) => _buildActivityRow(item)),
      ],
    );
  }

  Widget _buildActivityRow(Map<String, dynamic> item) {
    final tool = item['tool'] as String? ?? 'unknown';
    final success = item['success'] as bool? ?? false;
    final session = item['session_id'] as String? ?? '';
    final result = item['result'] as String? ?? '';
    final args = item['args'] as String? ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: success
              ? AppColors.success.withOpacity(0.2)
              : AppColors.danger.withOpacity(0.2),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            success ? Icons.check_circle_rounded : Icons.cancel_rounded,
            color: success ? AppColors.success : AppColors.danger,
            size: 16,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      tool,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                        fontFamily: 'Courier New',
                      ),
                    ),
                    if (session.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      Text(
                        session.length > 16
                            ? '${session.substring(0, 16)}…'
                            : session,
                        style: const TextStyle(
                          color: AppColors.textMuted,
                          fontSize: 10,
                          fontFamily: 'Courier New',
                        ),
                      ),
                    ],
                  ],
                ),
                if (args.isNotEmpty) ...[
                  const SizedBox(height: 3),
                  Text(
                    args.length > 100 ? '${args.substring(0, 100)}…' : args,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 11,
                      fontFamily: 'Courier New',
                    ),
                  ),
                ],
                if (result.isNotEmpty) ...[
                  const SizedBox(height: 3),
                  Text(
                    result.length > 120
                        ? '${result.substring(0, 120)}…'
                        : result,
                    style: TextStyle(
                      color: success
                          ? AppColors.textSecondary
                          : AppColors.danger.withOpacity(0.8),
                      fontSize: 11,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
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
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatCard({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              value,
              style: TextStyle(
                color: color,
                fontSize: 24,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: const TextStyle(
                  color: AppColors.textMuted, fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}