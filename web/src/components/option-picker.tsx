import { Pressable, StyleSheet, Text, View } from 'react-native';

import { colors, fontSizes, radius, spacing } from '@/theme';

export type Option<T extends string> = {
  value: T;
  label: string;
  description: string;
};

type Props<T extends string> = {
  label: string;
  options: Option<T>[];
  value: T;
  onChange: (value: T) => void;
};

// A list of choices where exactly one is selected, like radio buttons.
export function OptionPicker<T extends string>({ label, options, value, onChange }: Props<T>) {
  return (
    <View role="radiogroup" aria-label={label} style={styles.group}>
      <Text style={styles.label}>{label}</Text>
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <Pressable
            key={option.value}
            role="radio"
            aria-checked={selected}
            onPress={() => onChange(option.value)}
            style={[styles.option, selected && styles.selected]}>
            <Text style={styles.optionLabel}>{option.label}</Text>
            <Text style={styles.optionDescription}>{option.description}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  group: {
    gap: spacing.sm,
  },
  label: {
    fontSize: fontSizes.heading,
    fontWeight: '600',
    color: colors.text,
  },
  option: {
    padding: spacing.md,
    borderRadius: radius,
    borderWidth: 2,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  selected: {
    borderColor: colors.primary,
    backgroundColor: colors.selected,
  },
  optionLabel: {
    fontSize: fontSizes.body,
    fontWeight: '600',
    color: colors.text,
  },
  optionDescription: {
    marginTop: spacing.xs,
    fontSize: fontSizes.small,
    color: colors.textSecondary,
  },
});
