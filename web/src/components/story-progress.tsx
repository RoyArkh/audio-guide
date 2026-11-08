import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import type { StoryStatus } from '@/api';
import { colors, fontSizes, radius, spacing } from '@/theme';

// The pipeline stages in order, as reported by the API.
const STEPS: { status: StoryStatus; label: string }[] = [
  { status: 'finding_place', label: 'Finding the most interesting place nearby' },
  { status: 'researching', label: 'Reading up on its history' },
  { status: 'writing', label: 'Writing your story' },
  { status: 'generating_audio', label: 'Recording the audio' },
];

export function StoryProgress({ status }: { status: StoryStatus }) {
  const currentStep = STEPS.findIndex((step) => step.status === status);

  return (
    <View style={styles.card}>
      <Text style={styles.note}>
        {status === 'pending'
          ? 'Waiting for other stories to finish…'
          : 'This usually takes a minute or two. You can keep this page open.'}
      </Text>
      {STEPS.map((step, index) => {
        const done = index < currentStep;
        const active = index === currentStep;
        return (
          <View key={step.status} style={styles.step}>
            <View style={styles.marker}>
              {active ? (
                <ActivityIndicator size="small" color={colors.primary} />
              ) : (
                <Text style={done ? styles.check : styles.dot}>{done ? '✓' : '•'}</Text>
              )}
            </View>
            <Text style={[styles.label, !done && !active && styles.waiting]}>{step.label}</Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  note: {
    fontSize: fontSizes.small,
    color: colors.textSecondary,
  },
  step: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  marker: {
    width: 24,
    alignItems: 'center',
  },
  check: {
    fontSize: fontSizes.body,
    fontWeight: '700',
    color: colors.primary,
  },
  dot: {
    fontSize: fontSizes.body,
    color: colors.border,
  },
  label: {
    flexShrink: 1,
    fontSize: fontSizes.body,
    color: colors.text,
  },
  waiting: {
    color: colors.textSecondary,
  },
});
