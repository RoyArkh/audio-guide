import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { StyleSheet, Text, View } from 'react-native';

import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { formatTime } from '@/format';
import { colors, fontSizes, radius, spacing } from '@/theme';

const SKIP_SECONDS = 15;

type Props = {
  url: string;
  // From the API, shown until the browser has loaded the file and knows the real duration.
  durationSeconds: number;
};

export function AudioPlayer({ url, durationSeconds }: Props) {
  const player = useAudioPlayer(url);
  const status = useAudioPlayerStatus(player);
  const duration = status.duration || durationSeconds;
  const progress = duration > 0 ? Math.min(status.currentTime / duration, 1) : 0;

  // The buttons stay enabled before the file has loaded: iPhone Safari only loads audio after a tap.
  function togglePlay() {
    if (status.playing) {
      player.pause();
      return;
    }
    if (status.currentTime >= duration) {
      player.seekTo(0);
    }
    player.play();
  }

  function skip(seconds: number) {
    player.seekTo(Math.min(Math.max(status.currentTime + seconds, 0), duration));
  }

  return (
    <View style={styles.player}>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${progress * 100}%` }]} />
      </View>
      <View style={styles.times}>
        <Text style={styles.time}>{formatTime(status.currentTime)}</Text>
        <Text style={styles.time}>{formatTime(duration)}</Text>
      </View>
      <View style={styles.controls}>
        <View style={styles.control}>
          <Button title={`−${SKIP_SECONDS} s`} variant="secondary" onPress={() => skip(-SKIP_SECONDS)} />
        </View>
        <View style={styles.playControl}>
          <Button title={status.playing ? 'Pause' : 'Play'} onPress={togglePlay} />
        </View>
        <View style={styles.control}>
          <Button title={`+${SKIP_SECONDS} s`} variant="secondary" onPress={() => skip(SKIP_SECONDS)} />
        </View>
      </View>
      {status.error ? <ErrorMessage message={`Couldn't play the audio: ${status.error}`} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  player: {
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: radius,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  track: {
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.border,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    backgroundColor: colors.primary,
  },
  times: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  time: {
    fontSize: fontSizes.small,
    color: colors.textSecondary,
    fontVariant: ['tabular-nums'],
  },
  controls: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  control: {
    flex: 1,
  },
  playControl: {
    flex: 2,
  },
});
