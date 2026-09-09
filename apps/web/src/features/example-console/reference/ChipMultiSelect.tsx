import { useState, type Dispatch, type SetStateAction } from "react";
import visual from "./ChipMultiSelect.module.css";
import { Icon } from "./Icon";
import { INPUT_MONO } from "./inputMono";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const ChipMultiSelect = ({
  items,
  available,
  onAdd,
  onRemove,
  onFreeAdd,
}: {
  items: string[];
  available: string[];
  onAdd: (value: string) => void;
  onRemove: (value: string) => void;
  onFreeAdd?: ((value: string) => void) | undefined;
}) => {
  const [input, setInput] = useState("");
  const [pickerOpen, setPickerOpen] = useState(false);
  const unpicked = available.filter((x) => !items.includes(x));
  return (
    <div>
      <div className={visual.row}>
        {items.map((x) => (
          <span key={x} className={visual.row2}>
            {x}
            <button
              onClick={() => {
                onRemove(x);
              }}
              className={visual.row3}
            >
              <Icon name="x" size={9} />
            </button>
          </span>
        ))}
      </div>
      <ChipMultiSelectSection
        {...{ input, setInput, onFreeAdd, unpicked, setPickerOpen, pickerOpen, onAdd }}
      />
    </div>
  );
};

interface ChipMultiSelectSectionProps {
  input: string;
  setInput: Dispatch<SetStateAction<string>>;
  onFreeAdd: ((value: string) => void) | undefined;
  unpicked: string[];
  setPickerOpen: Dispatch<SetStateAction<boolean>>;
  pickerOpen: boolean;
  onAdd: (value: string) => void;
}

function ChipMultiSelectSection({
  input,
  setInput,
  onFreeAdd,
  unpicked,
  setPickerOpen,
  pickerOpen,
  onAdd,
}: ChipMultiSelectSectionProps) {
  return (
    <div className={visual.row4}>
      <ChipMultiSelectinput {...{ input, setInput, onFreeAdd }} />
      {unpicked.length > 0 && (
        <div className={visual.surface}>
          <button
            className="btn sm"
            onClick={() => {
              setPickerOpen((v) => !v);
            }}
          >
            <Icon name="menu" size={10} /> +{unpicked.length}
            <Icon name="chevron-d" size={9} />
          </button>
          {pickerOpen && (
            <div className={visual.overlay}>
              {unpicked.map((x) => (
                <button
                  key={x}
                  onClick={() => {
                    onAdd(x);
                    setPickerOpen(false);
                  }}
                  className={visual.action}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-hover)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <Icon name="plus" size={9} className={visual.surface2} />
                  {x}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface ChipMultiSelectinputProps {
  input: string;
  setInput: Dispatch<SetStateAction<string>>;
  onFreeAdd: ((value: string) => void) | undefined;
}

function ChipMultiSelectinput({ input, setInput, onFreeAdd }: ChipMultiSelectinputProps) {
  return (
    <input
      value={input}
      onChange={(e) => {
        setInput(e.target.value);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" && input.trim()) {
          onFreeAdd?.(input.trim());
          setInput("");
        }
      }}
      placeholder="+ custom · Enter"
      style={{ ...INPUT_MONO, flex: 1, height: 26, minWidth: 0 }}
    />
  );
}
