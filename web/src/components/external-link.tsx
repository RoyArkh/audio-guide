import { type Href, Link } from 'expo-router';
import type { ReactNode } from 'react';
import { StyleSheet } from 'react-native';

import { colors } from '@/theme';

// Opens in a new tab, so the story keeps playing.
export function ExternalLink({ url, children }: { url: string; children: ReactNode }) {
  return (
    <Link href={url as Href} target="_blank" rel="noopener noreferrer" style={styles.link}>
      {children}
    </Link>
  );
}

const styles = StyleSheet.create({
  link: {
    color: colors.primary,
    textDecorationLine: 'underline',
  },
});
