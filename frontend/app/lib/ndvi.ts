export type NdviGrid = (number | null)[][];

function ndviColor(value: number | null): [number, number, number, number] {
  if (value == null || Number.isNaN(value)) return [0, 0, 0, 0];
  if (value > 0.6) return [22, 163, 74, 200]; // deep green
  if (value >= 0.35) return [245, 158, 11, 200]; // amber
  return [146, 64, 14, 200]; // red-brown
}

export function gridToImageData(grid: NdviGrid): {
  width: number;
  height: number;
  data: Uint8ClampedArray;
} {
  const height = grid.length;
  const width = Math.max(0, ...grid.map((row) => row.length));
  const data = new Uint8ClampedArray(width * height * 4);
  for (let y = 0; y < height; y++) {
    const row = grid[y] ?? [];
    for (let x = 0; x < width; x++) {
      const value = row[x] ?? null;
      const [r, g, b, a] = ndviColor(value);
      const idx = (y * width + x) * 4;
      data[idx] = r;
      data[idx + 1] = g;
      data[idx + 2] = b;
      data[idx + 3] = a;
    }
  }
  return { width, height, data };
}
