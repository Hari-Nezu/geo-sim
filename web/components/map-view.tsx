"use client";

import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Circle, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Leaflet marker icon fix
const icon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

interface MapViewProps {
  selectedPoint: { lat: number; lng: number } | null;
  radius: number;
  onPointSelect: (point: { lat: number; lng: number }) => void;
}

function ClickHandler({ onPointSelect }: { onPointSelect: MapViewProps["onPointSelect"] }) {
  useMapEvents({
    click(e) {
      onPointSelect({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });
  return null;
}

export default function MapView({ selectedPoint, radius, onPointSelect }: MapViewProps) {
  return (
    <MapContainer
      center={[35.6812, 139.7671]}
      zoom={13}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClickHandler onPointSelect={onPointSelect} />
      {selectedPoint && (
        <>
          <Marker position={[selectedPoint.lat, selectedPoint.lng]} icon={icon} />
          <Circle
            center={[selectedPoint.lat, selectedPoint.lng]}
            radius={radius}
            pathOptions={{ color: "#2563eb", fillOpacity: 0.08 }}
          />
        </>
      )}
    </MapContainer>
  );
}
