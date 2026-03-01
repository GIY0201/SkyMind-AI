import { useState } from "react";
import { useDroneState } from "../hooks/useDroneState";

/** 레이어 정의 */
const LAYERS = [
  { key: "airspaceRestricted", label: "Restricted", color: "bg-red-500", group: "Airspace" },
  { key: "airspaceControlled", label: "Controlled", color: "bg-yellow-500", group: "Airspace" },
  { key: "airspaceFree", label: "Free Zone", color: "bg-green-500", group: "Airspace" },
  { key: "droneMarkers", label: "Drones", color: "bg-blue-400", group: "Data" },
  { key: "flightTrails", label: "Trails", color: "bg-cyan-400", group: "Data" },
  { key: "weatherOverlay", label: "Weather", color: "bg-purple-400", group: "Data" },
  { key: "landingZones", label: "Landing", color: "bg-lime-400", group: "Data" },
] as const;

function MapLayerControl() {
  const [open, setOpen] = useState(false);
  const layerVisibility = useDroneState((s) => s.layerVisibility);
  const setLayerVisibility = useDroneState((s) => s.setLayerVisibility);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="ui-overlay top-14 right-[22rem] w-10 h-10 rounded-lg bg-gray-800/95 border border-gray-700 flex items-center justify-center hover:bg-gray-700 transition-colors"
        title="레이어 컨트롤"
      >
        <svg className="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      </button>
    );
  }

  const groups = ["Airspace", "Data"];

  return (
    <div className="ui-overlay top-14 right-[22rem] w-48 bg-gray-800/95 rounded-lg shadow-xl border border-gray-700 text-sm">
      {/* 헤더 */}
      <div className="px-3 py-2 border-b border-gray-700 flex items-center justify-between">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Layers</h3>
        <button
          onClick={() => setOpen(false)}
          className="text-gray-500 hover:text-gray-300 p-0.5"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* 레이어 목록 */}
      <div className="px-3 py-2 space-y-2">
        {groups.map((group) => (
          <div key={group}>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{group}</div>
            {LAYERS.filter((l) => l.group === group).map((layer) => {
              const visible = layerVisibility[layer.key as keyof typeof layerVisibility];
              return (
                <label
                  key={layer.key}
                  className="flex items-center gap-2 py-0.5 cursor-pointer hover:bg-gray-700/50 rounded px-1 -mx-1"
                >
                  <span className={`w-2 h-2 rounded-full ${layer.color} ${!visible ? "opacity-30" : ""}`} />
                  <span className={`flex-1 text-xs ${visible ? "text-gray-300" : "text-gray-500"}`}>
                    {layer.label}
                  </span>
                  <input
                    type="checkbox"
                    checked={visible}
                    onChange={(e) => setLayerVisibility(layer.key, e.target.checked)}
                    className="w-3.5 h-3.5 rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-0 focus:ring-offset-0 cursor-pointer"
                  />
                </label>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export default MapLayerControl;
