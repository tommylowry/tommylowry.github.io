import React from 'react';

export function PlayerRow({ player }) {
  const ffWarStyle = (v) => {
    if (v > 0) return { color: 'green' };
    if (v < 0) return { color: 'red' };
    return { color: '#555' };
  };

  return (
    <tr style={{ borderBottom: '1px solid #ddd' }}>
      <td>{player.key}</td>
      <td>{player.position}</td>
      <td align="center">{player.total_points}</td>
      <td align="center" style={ffWarStyle(player.ffWAR)}>{player.ffWAR}</td>
    </tr>
  );
}