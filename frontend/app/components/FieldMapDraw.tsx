"use client";

import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import L from "leaflet";
import "leaflet-draw";
import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import { IMAGERY_ATTRIBUTION, IMAGERY_URL, LABELS_URL } from "../lib/mapTiles";
import { toWktPolygon } from "../lib/wkt";

// Central Valley default view — most pilot farms are CA (CONUS-only product).
const DEFAULT_CENTER: [number, number] = [36.9, -119.9];
const DEFAULT_ZOOM = 6;
// Close enough to trace a field edge off the imagery.
const LOCATE_ZOOM = 16;

// Leaflet touches `window` at import time, so this component must only be
// loaded with next/dynamic({ ssr: false }).
export default function FieldMapDraw({
  onChange,
  onDrawingChange,
}: {
  onChange: (wkt: string | null) => void;
  onDrawingChange?: (drawing: boolean) => void;
}) {
  return (
    // relative z-0 isolate traps Leaflet's internal z-indexes (up to ~1000)
    // so the map can't paint over modal overlays
    <div className="relative isolate z-0 h-80 overflow-hidden rounded-xl">
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        className="h-full w-full"
      >
        <TileLayer attribution={IMAGERY_ATTRIBUTION} url={IMAGERY_URL} />
        <TileLayer url={LABELS_URL} />
        <DrawControl onChange={onChange} onDrawingChange={onDrawingChange} />
        <LocateButton />
      </MapContainer>
    </div>
  );
}

function LocateButton() {
  const map = useMap();
  const t = useTranslations("fieldMap");
  const [locating, setLocating] = useState(false);
  const [failed, setFailed] = useState(false);

  const locate = () => {
    if (!("geolocation" in navigator)) {
      setFailed(true);
      return;
    }
    setLocating(true);
    setFailed(false);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        map.flyTo([pos.coords.latitude, pos.coords.longitude], LOCATE_ZOOM);
      },
      () => {
        setLocating(false);
        setFailed(true);
      },
      { enableHighAccuracy: true, timeout: 10_000 },
    );
  };

  return (
    // z-[1000] sits above Leaflet's tile/control panes
    <div className="absolute right-3 top-3 z-[1000] flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={locate}
        disabled={locating}
        className="rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-md hover:bg-gray-50 disabled:opacity-60"
      >
        {locating ? t("locating") : `📍 ${t("locate")}`}
      </button>
      {failed && (
        <span
          role="alert"
          className="max-w-48 rounded-lg bg-white/95 px-2 py-1 text-right text-xs text-red-600 shadow"
        >
          {t("locateError")}
        </span>
      )}
    </div>
  );
}

function DrawControl({
  onChange,
  onDrawingChange,
}: {
  onChange: (wkt: string | null) => void;
  onDrawingChange?: (drawing: boolean) => void;
}) {
  const map = useMap();
  // Latest-callback ref: the draw handlers below are bound once, so they read
  // onChange through a ref kept current outside of render (react-hooks/refs).
  const onChangeRef = useRef(onChange);
  const onDrawingChangeRef = useRef(onDrawingChange);
  useEffect(() => {
    onChangeRef.current = onChange;
    onDrawingChangeRef.current = onDrawingChange;
  }, [onChange, onDrawingChange]);

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
    const onDrawStart = () => onDrawingChangeRef.current?.(true);
    const onDrawStop = () => onDrawingChangeRef.current?.(false);
    map.on(L.Draw.Event.CREATED, onCreated);
    map.on(L.Draw.Event.EDITED, emit);
    map.on(L.Draw.Event.DELETED, emit);
    map.on(L.Draw.Event.DRAWSTART, onDrawStart);
    map.on(L.Draw.Event.DRAWSTOP, onDrawStop);

    return () => {
      map.off(L.Draw.Event.CREATED, onCreated);
      map.off(L.Draw.Event.EDITED, emit);
      map.off(L.Draw.Event.DELETED, emit);
      map.off(L.Draw.Event.DRAWSTART, onDrawStart);
      map.off(L.Draw.Event.DRAWSTOP, onDrawStop);
      map.removeControl(control);
      map.removeLayer(drawn);
    };
  }, [map]);

  return null;
}
