import { StyleSheet, Text } from 'react-native';

import { colors, fontSizes, radius, spacing } from '@/theme';

export function ErrorMessage({ message }: { message: string }) {
  return (
    <Text role="alert" style={styles.error}>
      {message}
    </Text>
  );
}

const styles = StyleSheet.create({
  error: {
    padding: spacing.md,
    borderRadius: radius,
    backgroundColor: colors.errorBackground,
    color: colors.error,
    fontSize: fontSizes.body,
    lineHeight: 22,
  },
});
