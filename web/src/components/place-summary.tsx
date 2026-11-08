import { StyleSheet, Text, View } from 'react-native';

import type { Place } from '@/api';
import { formatDistance } from '@/format';
import { colors, fontSizes, spacing } from '@/theme';

export function PlaceSummary({ place }: { place: Place }) {
  const where = place.at_place
    ? "You're at"
    : `Nearest notable place, ${formatDistance(place.distance_m)} away`;

  return (
    <View style={styles.summary}>
      <Text style={styles.where}>{where}</Text>
      <Text role="heading" style={styles.name}>
        {place.name}
      </Text>
      {place.description ? <Text style={styles.description}>{place.description}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  summary: {
    gap: spacing.xs,
  },
  where: {
    fontSize: fontSizes.small,
    color: colors.textSecondary,
  },
  name: {
    fontSize: fontSizes.title,
    fontWeight: '700',
    color: colors.text,
  },
  description: {
    fontSize: fontSizes.body,
    color: colors.textSecondary,
  },
});
