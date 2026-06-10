"use client";

import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import L from "leaflet";
import "leaflet-draw";
import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import { toWktPolygon } from "../lib/wkt";

// Central Valley default view — most pilot farms are CA (CONUS-only product).
const DEFAULT_CENTER: [number, number] = [36.9, -119.9];
const DEFAULT_ZOOM = 6;

// Leaflet touches `window` at import time, so this component must only be
// loaded with next/dynamic({ ssr: false }).
export default function FieldMapDraw({
  onChange,
}: {
  onChange: (wkt: string | null) => void;
}) {
  return (
    // relative z-0 isolate traps Leaflet's internal z-indexes (up to ~1000)
    // so the map can't paint over modal overlays
    <div className="relative isolate z-0 h-64 overflow-hidden rounded-xl">
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <DrawControl onChange={onChange} />
      </MapContainer>
    </div>
  );
}

function DrawControl({ onChange }: { onChange: (wkt: string | null) => void }) {
  const map = useMap();
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    const drawn = new L.FeatureGroup();
    map.addLayer(drawn);
    const control = new L.Control.Draw({
      draw: {
        polygon: { allowIntersection: false },
        polyline: false,
        rectangle: false,
        circle: false,
        circlemarker: false,
        marker: false,
      },
      edit: { featureGroup: drawn },
    });
    map.addControl(control);

    const emit = () => {
      const layer = drawn.getLayers()[0] as L.Polygon | undefined;
      if (!layer) {
        onChangeRef.current(null);
        return;
      }
      const ring = layer.getLatLngs()[0] as L.LatLng[];
      onChangeRef.current(toWktPolygon(ring.map((p) => [p.lat, p.lng])));
    };

    const onCreated = (event: L.LeafletEvent) => {
      // One field boundary per farm — replace any previous drawing.
      drawn.clearLayers();
      drawn.addLayer((event as L.DrawEvents.Created).layer);
      emit();
    };
    map.on(L.Draw.Event.CREATED, onCreated);
    map.on(L.Draw.Event.EDITED, emit);
    map.on(L.Draw.Event.DELETED, emit);

    return () => {
      map.off(L.Draw.Event.CREATED, onCreated);
      map.off(L.Draw.Event.EDITED, emit);
      map.off(L.Draw.Event.DELETED, emit);
      map.removeControl(control);
      map.removeLayer(drawn);
    };
  }, [map]);

  return null;
}
