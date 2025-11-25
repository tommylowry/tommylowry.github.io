import React from 'react';
import { Link } from 'react-router-dom';
import { toPlayerSlug } from './player/PlayerNameFormatter';

export function displayFromSlug(slug) {
  if (!slug) return '';
  const decoded = decodeURIComponent(slug);
  return decoded
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

export function PlayerRow({ player }) {
  const slug = toPlayerSlug(player.key); // preserves capitalization
  const war = Number(player.ffWAR);
  const warClass = war > 0 ? 'war-positive' : war < 0 ? 'war-negative' : 'war-neutral';

  return (
    <tr>
      <td align="center">
        <Link to={`/player/${slug}`}>{player.key}</Link>
      </td>
      <td align="center">{player.position}</td>
      <td align="center">{player.total_points}</td>
      <td align="center" className={warClass}>{player.ffWAR}</td>
    </tr>
  );
}