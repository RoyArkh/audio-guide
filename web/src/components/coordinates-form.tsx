import { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';

import type { Coordinates } from '@/api';
import { Button } from '@/components/button';
import { colors, fontSizes, radius, spacing } from '@/theme';

const EXAMPLES = [
  { name: 'Eiffel Tower', coordinates: { lat: 48.8584, lng: 2.2945 } },
  { name: 'Colosseum', coordinates: { lat: 41.8902, lng: 12.4922 } },
  { name: 'Times Square', coordinates: { lat: 40.758, lng: -73.9855 } },
];

type Props = {
  onSubmit: (coordinates: Coordinates) => void;
  disabled: boolean;
};

// For when location access is blocked, or to try places you're not at.
export function CoordinatesForm({ onSubmit, disabled }: Props) {
  const [text, setText] = useState('');
  const [error, setError] = useState<string | null>(null);

  function submit() {
    const coordinates = parseCoordinates(text);
    if (!coordinates) {
      setError('Enter latitude and longitude separated by a comma, e.g. 48.8584, 2.2945');
      return;
    }
    setError(null);
    onSubmit(coordinates);
  }

  return (
    <View style={styles.form}>
      <Text style={styles.heading}>Or pick a spot yourself</Text>
      <Text style={styles.hint}>
        Paste coordinates, for example from Google Maps (right-click a spot to copy them).
      </Text>
      <TextInput
        value={text}
        onChangeText={setText}
        onSubmitEditing={submit}
        placeholder="48.8584, 2.2945"
        placeholderTextColor={colors.textSecondary}
        aria-label="Latitude and longitude"
        inputMode="decimal"
        autoCorrect={false}
        style={styles.input}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <Button title="Use these coordinates" variant="secondary" onPress={submit} disabled={disabled} />

      <Text style={styles.hint}>Or try a famous place:</Text>
      <View style={styles.examples}>
        {EXAMPLES.map((example) => (
          <Button
            key={example.name}
            title={example.name}
            variant="secondary"
            onPress={() => onSubmit(example.coordinates)}
            disabled={disabled}
          />
        ))}
      </View>
    </View>
  );
}

// "48.8584, 2.2945" -> { lat: 48.8584, lng: 2.2945 }, or null if it isn't valid.
function parseCoordinates(text: string): Coordinates | null {
  const parts = text.split(',').map((part) => part.trim());
  if (parts.length !== 2 || parts.some((part) => part === '')) {
    return null;
  }
  const [lat, lng] = parts.map(Number);
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) {
    return null;
  }
  return { lat, lng };
}

const styles = StyleSheet.create({
  form: {
    gap: spacing.sm,
  },
  heading: {
    fontSize: fontSizes.heading,
    fontWeight: '600',
    color: colors.text,
  },
  hint: {
    fontSize: fontSizes.small,
    color: colors.textSecondary,
  },
  input: {
    minHeight: 48,
    paddingHorizontal: spacing.md,
    borderRadius: radius,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    fontSize: fontSizes.body,
    color: colors.text,
  },
  error: {
    fontSize: fontSizes.small,
    color: colors.error,
  },
  examples: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
});
