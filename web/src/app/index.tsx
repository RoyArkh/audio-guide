import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { type Coordinates, createStory, findNearbyPlace, type Length, type Mood, type Place } from '@/api';
import { Button } from '@/components/button';
import { CoordinatesForm } from '@/components/coordinates-form';
import { ErrorMessage } from '@/components/error-message';
import { OptionPicker } from '@/components/option-picker';
import { Page } from '@/components/page';
import { PlaceSummary } from '@/components/place-summary';
import { errorMessage } from '@/format';
import { getCurrentLocation } from '@/location';
import { LENGTHS, MOODS } from '@/story-options';
import { colors, fontSizes, spacing } from '@/theme';

type Found = { coordinates: Coordinates; place: Place };

// Step 1: find where the listener is. Step 2: pick a length and mood, and start the story.
export default function HomeScreen() {
  const [found, setFound] = useState<Found | null>(null);
  const [looking, setLooking] = useState(false);
  const [length, setLength] = useState<Length>('short');
  const [mood, setMood] = useState<Mood>('historical');
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function findPlace(locate: () => Promise<Coordinates>) {
    setError(null);
    setLooking(true);
    try {
      const coordinates = await locate();
      const place = await findNearbyPlace(coordinates);
      setFound({ coordinates, place });
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setLooking(false);
    }
  }

  async function startStory(coordinates: Coordinates) {
    setError(null);
    setStarting(true);
    try {
      const jobId = await createStory(coordinates, length, mood);
      router.push(`/story/${jobId}`);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setStarting(false);
    }
  }

  function changePlace() {
    setError(null);
    setFound(null);
  }

  if (found) {
    return (
      <Page>
        <PlaceSummary place={found.place} />
        <Button title="Change place" variant="secondary" onPress={changePlace} />
        <OptionPicker label="Story length" options={LENGTHS} value={length} onChange={setLength} />
        <OptionPicker label="Mood" options={MOODS} value={mood} onChange={setMood} />
        {error ? <ErrorMessage message={error} /> : null}
        <Button
          title={starting ? 'Starting…' : 'Make my story'}
          onPress={() => startStory(found.coordinates)}
          disabled={starting}
        />
      </Page>
    );
  }

  return (
    <Page>
      <View style={styles.intro}>
        <Text role="heading" style={styles.title}>
          Hear the story of where you're standing
        </Text>
        <Text style={styles.text}>
          Share your location, choose a length and a mood, and get a short audio story about the
          most interesting place nearby.
        </Text>
      </View>

      <Button title="Use my location" onPress={() => findPlace(getCurrentLocation)} disabled={looking} />
      {looking ? (
        <View style={styles.looking}>
          <ActivityIndicator color={colors.primary} />
          <Text style={styles.text}>Looking for notable places nearby…</Text>
        </View>
      ) : null}
      {error ? <ErrorMessage message={error} /> : null}

      <CoordinatesForm onSubmit={(coordinates) => findPlace(async () => coordinates)} disabled={looking} />
    </Page>
  );
}

const styles = StyleSheet.create({
  intro: {
    gap: spacing.sm,
  },
  title: {
    fontSize: fontSizes.title,
    fontWeight: '700',
    color: colors.text,
  },
  text: {
    fontSize: fontSizes.body,
    lineHeight: 24,
    color: colors.textSecondary,
  },
  looking: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
});
