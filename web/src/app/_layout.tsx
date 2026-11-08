import { Stack } from 'expo-router';

import { colors } from '@/theme';

export default function RootLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        title: 'Audio Guide',
        contentStyle: { backgroundColor: colors.background },
      }}
    />
  );
}
