import { useState, type Dispatch, type SetStateAction } from "react";
import type * as E from "../exampleTypes";
import visual from "./FileNode.module.css";
import { Icon } from "./Icon";

/** Reference: screens/Workspace.jsx; EXAMPLE ONLY. */
export const FileNode = ({
  node,
  depth,
  selected,
  onSelect,
}: {
  node: E.FileEntry;
  depth: number;
  selected: string;
  onSelect: (name: string) => void;
}) => {
  const [open, setOpen] = useState(true);
  const isFile = node.type === "file";
  const isSelected = selected === node.path;
  return (
    <FileNodeContent {...{ depth, isSelected, node, isFile, onSelect, setOpen, open, selected }} />
  );
};

interface FileNodeContentProps {
  depth: number;
  isSelected: boolean;
  node: E.FileEntry;
  isFile: boolean;
  onSelect: (name: string) => void;
  setOpen: Dispatch<SetStateAction<boolean>>;
  open: boolean;
  selected: string;
}

function FileNodeContent({
  depth,
  isSelected,
  node,
  isFile,
  onSelect,
  setOpen,
  open,
  selected,
}: FileNodeContentProps) {
  return (
    <>
      <FileNodeSection {...{ depth, isSelected, node, isFile, onSelect, setOpen, open }} />
      {!isFile &&
        open &&
        node.children?.map((child) => (
          <FileNode
            key={child.path}
            node={child}
            depth={depth + 1}
            selected={selected}
            onSelect={onSelect}
          />
        ))}
    </>
  );
}

interface FileNodeSectionProps {
  depth: number;
  isSelected: boolean;
  node: E.FileEntry;
  isFile: boolean;
  onSelect: (name: string) => void;
  setOpen: Dispatch<SetStateAction<boolean>>;
  open: boolean;
}

function FileNodeSection({
  depth,
  isSelected,
  node,
  isFile,
  onSelect,
  setOpen,
  open,
}: FileNodeSectionProps) {
  return (
    <div
      className={visual.grid}
      style={{
        paddingLeft: 8 + depth * 14,
        background: isSelected ? "var(--bg-hover)" : "transparent",
        color: node.highlight ? "var(--accent)" : "var(--fg-muted)",
      }}
      onClick={() => {
        if (isFile) onSelect(node.path);
        else setOpen(!open);
      }}
    >
      <span className={visual.row}>
        {!isFile && <Icon name={open ? "chevron-d" : "chevron-r"} size={9} />}
        {isFile && <span className={visual.surface} />}
        <Icon name={isFile ? "book" : "hex"} size={10} className={visual.surface2} />
        <span>
          {node.path.split("/").filter(Boolean).pop()}
          {!isFile && "/"}
        </span>
      </span>
      {isFile && <span className={visual.caption}>{node.size}</span>}
      {isFile && <span className={visual.caption2}>{node.modified}</span>}
    </div>
  );
}
