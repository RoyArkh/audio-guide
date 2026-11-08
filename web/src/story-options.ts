import type { Length, Mood } from '@/api';
import type { Option } from '@/components/option-picker';

export const LENGTHS: Option<Length>[] = [
  { value: 'short', label: 'Short', description: 'About 2 minutes' },
  { value: 'medium', label: 'Medium', description: 'About 5 minutes' },
  { value: 'long', label: 'Long', description: 'About 10 minutes' },
];

export const MOODS: Option<Mood>[] = [
  { value: 'historical', label: 'Historical', description: 'Just the facts' },
  {
    value: 'historical_emotional',
    label: 'Historical + emotional',
    description: 'Facts, fun details, a few light jokes and some moving moments',
  },
  { value: 'romantic', label: 'Romantic', description: 'Fun facts, love stories and legends' },
];
