import { router, useLocalSearchParams } from 'expo-router';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { fullUrl, isFinished, type Source, type Story } from '@/api';
import { AudioPlayer } from '@/components/audio-player';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { ExternalLink } from '@/components/external-link';
import { Page } from '@/components/page';
import { PlaceSummary } from '@/components/place-summary';
import { StoryProgress } from '@/components/story-progress';
import { colors, fontSizes, spacing } from '@/theme';
import { useStory } from '@/use-story';

// The page has its own URL, so it survives a refresh and can be shared.
export default function StoryScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { story, error, connectionProblem } = useStory(id);
  const finished = error !== null || (story !== null && isFinished(story.status));

  return (
    <Page>
      {error ? <ErrorMessage message={error} /> : null}
      {!story && !error ? <ActivityIndicator color={colors.primary} /> : null}
      {story?.place ? <PlaceSummary place={story.place} /> : null}
      {story ? <StoryBody story={story} /> : null}
      {connectionProblem ? <Text style={styles.note}>Connection problem, still trying…</Text> : null}
      {finished ? (
        <Button title="Make another story" variant="secondary" onPress={() => router.navigate('/')} />
      ) : null}
    </Page>
  );
}

function StoryBody({ story }: { story: Story }) {
  if (story.status === 'failed') {
    return <ErrorMessage message={`Sorry, the story couldn't be made: ${story.error}`} />;
  }
  if (story.status === 'done') {
    return (
      <>
        <AudioPlayer url={fullUrl(story.audio_url ?? '')} durationSeconds={story.duration_seconds ?? 0} />
        <Transcript text={story.transcript ?? ''} />
        <Sources sources={story.sources} />
      </>
    );
  }
  return <StoryProgress status={story.status} />;
}

function Transcript({ text }: { text: string }) {
  const paragraphs = text
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter((paragraph) => paragraph !== '');

  return (
    <View style={styles.section}>
      <Text role="heading" style={styles.heading}>
        Transcript
      </Text>
      {paragraphs.map((paragraph, index) => (
        <Text key={index} style={styles.paragraph}>
          {paragraph}
        </Text>
      ))}
    </View>
  );
}

// Wikipedia text is CC BY-SA, so stories based on it credit the article and its license.
function Sources({ sources }: { sources: Source[] }) {
  return (
    <View style={styles.section}>
      <Text role="heading" style={styles.heading}>
        Sources
      </Text>
      {sources.map((source) => (
        <Text key={source.url} style={styles.source}>
          <ExternalLink url={source.url}>{source.title}</ExternalLink>, {source.license}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    gap: spacing.sm,
  },
  heading: {
    fontSize: fontSizes.heading,
    fontWeight: '600',
    color: colors.text,
  },
  paragraph: {
    fontSize: fontSizes.body,
    lineHeight: 26,
    color: colors.text,
  },
  source: {
    fontSize: fontSizes.small,
    color: colors.textSecondary,
  },
  note: {
    fontSize: fontSizes.small,
    color: colors.textSecondary,
  },
});
