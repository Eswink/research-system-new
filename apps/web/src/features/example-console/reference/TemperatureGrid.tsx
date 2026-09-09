import { useState, type Dispatch, type SetStateAction } from "react";
import { Icon } from "./Icon";
import { INPUT_MONO } from "./inputMono";
import visual from "./TemperatureGrid.module.css";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const TemperatureGrid = ({
  values,
  onChange,
}: {
  values: number[];
  onChange: (values: number[]) => void;
}) => {
  const [newVal, setNewVal] = useState(0.4);
  const sorted = [...values].sort((a, b) => a - b);
  return (
    <div>
      {/* Sample point track */}
      <div className={visual.indicator}>
        {/* Ticks */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((t) => (
          <div
            key={t}
            className={visual.overlay}
            style={{ left: `calc(12px + ${String(t * 100)}% - ${String(t * 24)}px)` }}
          />
        ))}
        {/* Baseline */}
        <div className={visual.overlay2} />
        {/* Dots */}
        {sorted.map((v, i) => (
          <div
            key={i}
            title={`temperature = ${v.toFixed(2)}`}
            className={visual.overlay3}
            style={{ left: `calc(12px + ${String(v * 100)}% - ${String(v * 24)}px)` }}
          />
        ))}
        {/* labels */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((t) => (
          <div
            key={t}
            className={visual.caption}
            style={{ left: `calc(12px + ${String(t * 100)}% - ${String(t * 24)}px)` }}
          >
            {t.toFixed(2)}
          </div>
        ))}
      </div>

      {/* Chips */}
      <TemperatureGridSection {...{ sorted, onChange, values, newVal, setNewVal }} />
    </div>
  );
};

interface TemperatureGridSectionProps {
  sorted: number[];
  onChange: (values: number[]) => void;
  values: number[];
  newVal: number;
  setNewVal: Dispatch<SetStateAction<number>>;
}

function TemperatureGridSection({
  sorted,
  onChange,
  values,
  newVal,
  setNewVal,
}: TemperatureGridSectionProps) {
  return (
    <div className={visual.row}>
      {sorted.map((v, i) => (
        <span key={i} className={visual.row2}>
          {v.toFixed(2)}
          <button
            onClick={() => {
              onChange(values.filter((x) => x !== v));
            }}
            className={visual.row3}
          >
            <Icon name="x" size={9} />
          </button>
        </span>
      ))}
      <div className={visual.row4}>
        <input
          type="number"
          step="0.05"
          min="0"
          max="1"
          value={newVal}
          onChange={(e) => {
            setNewVal(Number(e.target.value));
          }}
          style={{ ...INPUT_MONO, height: 22, width: 60, fontSize: 11, padding: "0 6px" }}
        />
        <button
          className={`btn sm ${visual.action ?? ""}`}
          onClick={() => {
            if (!values.includes(newVal) && newVal >= 0 && newVal <= 1)
              onChange([...values, newVal]);
          }}
        >
          <Icon name="plus" size={9} /> add
        </button>
      </div>
    </div>
  );
}
