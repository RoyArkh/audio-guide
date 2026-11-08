import { Link } from 'expo-router';
import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';

import { colors, fontSizes, maxContentWidth, spacing } from '@/theme';

// A scrollable, centred column with the app name on top.
export function Page({ children }: { children: ReactNode }) {
  return (
    <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
      <View style={styles.column}>
        <Link href="/" style={styles.appName}>
          Audio Guide
        </Link>
        {children}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    alignItems: 'center',
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  column: {
    width: '100%',
    maxWidth: maxContentWidth,
    gap: spacing.lg,
  },
  appName: {
    fontSize: fontSizes.small,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: colors.primary,
  },
});
