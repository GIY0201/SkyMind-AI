import { useState, useEffect, useCallback } from "react";
import { useCesium } from "resium";
import {
  Cartesian3,
  Math as CesiumMath,
  Cartographic,
  SceneMode,
} from "cesium";

/** 빠른 이동 위치 목록 */
const LOCATIONS = [
  { label: "서울", lon: 126.978, lat: 37.5665, alt: 15000 },
  { label: "김포공항", lon: 126.7906, lat: 37.5586, alt: 8000 },
  { label: "인천공항", lon: 126.4407, lat: 37.4602, alt: 12000 },
  { label: "부산", lon: 129.0756, lat: 35.1796, alt: 20000 },
  { label: "제주", lon: 126.5312, lat: 33.4996, alt: 20000 },
] as const;

function MapControls() {
  const { viewer } = useCesium();
  const [coords, setCoords] = useState<{ lat: number; lon: number; alt: number } | null>(null);
  const [expanded, setExpanded] = useState(false);

  // 카메라 이동
  const flyTo = useCallback(
    (lon: number, lat: number, alt: number) => {
      if (!viewer) return;
      viewer.camera.flyTo({
        destination: Cartesian3.fromDegrees(lon, lat, alt),
        duration: 1.5,
      });
    },
    [viewer]
  );

  // 마우스 좌표 추적 (100ms 쓰로틀)
  useEffect(() => {
    if (!viewer) return;

    const scene = viewer.scene;
    const canvas = scene.canvas;
    let lastUpdate = 0;

    const handler = (e: MouseEvent) => {
      const now = Date.now();
      if (now - lastUpdate < 100) return;
      lastUpdate = now;

      if (scene.mode === SceneMode.MORPHING) return;

      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const ray = scene.camera.getPickRay(
        new Cartesian3(x * window.devicePixelRatio, y * window.devicePixelRatio, 0)
      );
      if (!ray) return;

      const cartesian = scene.globe.pick(ray, scene);
      if (!cartesian) return;

      const carto = Cartographic.fromCartesian(cartesian);
      setCoords({
        lat: CesiumMath.toDegrees(carto.latitude),
        lon: CesiumMath.toDegrees(carto.longitude),
        alt: carto.height,
      });
    };

    canvas.addEventListener("mousemove", handler);
    return () => canvas.removeEventListener("mousemove", handler);
  }, [viewer]);

  return (
    <div
      className="ui-overlay bottom-4 right-4"
      style={{ pointerEvents: "auto" }}
    >
      {/* 좌표 표시 바 */}
      {coords && (
        <div className="mb-2 px-3 py-1.5 bg-gray-800/95 rounded-lg border border-gray-700 text-xs font-mono text-gray-300 flex gap-3">
          <span>{coords.lat.toFixed(5)}°N</span>
          <span>{coords.lon.toFixed(5)}°E</span>
          <span>{coords.alt.toFixed(0)}m</span>
        </div>
      )}

      {/* 빠른 이동 */}
      {expanded ? (
        <div className="bg-gray-800/95 rounded-lg border border-gray-700 overflow-hidden">
          <div className="px-3 py-1.5 border-b border-gray-700 flex items-center justify-between">
            <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Quick Nav</span>
            <button
              onClick={() => setExpanded(false)}
              className="text-gray-500 hover:text-gray-300"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="p-1.5 grid grid-cols-1 gap-0.5">
            {LOCATIONS.map((loc) => (
              <button
                key={loc.label}
                onClick={() => flyTo(loc.lon, loc.lat, loc.alt)}
                className="px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 rounded transition-colors text-left"
              >
                {loc.label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <button
          onClick={() => setExpanded(true)}
          className="w-10 h-10 rounded-lg bg-gray-800/95 border border-gray-700 flex items-center justify-center hover:bg-gray-700 transition-colors"
          title="빠른 이동"
        >
          <svg className="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      )}
    </div>
  );
}

export default MapControls;
