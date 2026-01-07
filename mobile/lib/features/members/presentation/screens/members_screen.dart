import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/members/members_state.dart';
import '../../../../core/projects/project_state.dart';
import '../widgets/add_member_modal.dart';

class MembersScreen extends ConsumerStatefulWidget {
  const MembersScreen({super.key});

  @override
  ConsumerState<MembersScreen> createState() => _MembersScreenState();
}

class _MembersScreenState extends ConsumerState<MembersScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      final currentProject = ref.read(projectProvider).currentProject;
      if (currentProject != null) {
        ref.read(membersProvider.notifier).loadMembers(currentProject.id);
      }
    });
  }

  void _showAddMemberModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: const AddMemberModal(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final membersState = ref.watch(membersProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Members'),
        actions: [
          IconButton(
            key: const Key('add_member_button'),
            icon: const Icon(Icons.person_add_outlined),
            onPressed: _showAddMemberModal,
            tooltip: 'Add Member',
          ),
        ],
      ),
      body: membersState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : membersState.members.isEmpty
              ? _buildEmptyState()
              : _buildMembersList(membersState.members),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.group_outlined,
              size: 80,
              color: Theme.of(context).colorScheme.outline,
            ),
            const SizedBox(height: 16),
            Text(
              'No members yet',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'Add members to collaborate on this project',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _showAddMemberModal,
              icon: const Icon(Icons.person_add),
              label: const Text('Add Member'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMembersList(List<Member> members) {
    return RefreshIndicator(
      onRefresh: () async {
        final currentProject = ref.read(projectProvider).currentProject;
        if (currentProject != null) {
          await ref.read(membersProvider.notifier).loadMembers(currentProject.id);
        }
      },
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: members.length,
        itemBuilder: (context, index) {
          final member = members[index];
          return _MemberTile(member: member);
        },
      ),
    );
  }
}

class _MemberTile extends StatelessWidget {
  final Member member;

  const _MemberTile({required this.member});

  @override
  Widget build(BuildContext context) {
    final isOwner = member.role.toLowerCase() == 'owner';

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: isOwner
            ? Theme.of(context).colorScheme.primaryContainer
            : Theme.of(context).colorScheme.surfaceContainerHighest,
        child: Icon(
          Icons.person,
          color: isOwner
              ? Theme.of(context).colorScheme.onPrimaryContainer
              : Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      ),
      title: Text(
        member.name ?? member.email,
        style: const TextStyle(fontWeight: FontWeight.w500),
      ),
      subtitle: member.name != null ? Text(member.email) : null,
      trailing: isOwner
          ? Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                'Owner',
                style: TextStyle(
                  fontSize: 12,
                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                ),
              ),
            )
          : null,
    );
  }
}
