import visual from "./YamlView.module.css";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const YamlView = ({ text }: { text: string }) => (
  <div className={visual.surface}>
    <pre className={visual.label}>
      {text.split("\n").map((line, i) => {
        const kwMatch = /^(\s*)([\w_]+):/.exec(line);
        const commentMatch = /(.*)(#.*)$/.exec(line);
        let content;
        if (commentMatch) {
          content = (
            <>
              <span>{commentMatch[1]}</span>
              <span className={visual.surface2}>{commentMatch[2]}</span>
            </>
          );
        } else if (kwMatch) {
          const [, indent = "", key = ""] = kwMatch;
          const rest = line.slice(indent.length + key.length + 1);
          content = (
            <>
              <span>{indent}</span>
              <span className={visual.surface3}>{key}</span>:
              <span className={visual.surface4}>{rest}</span>
            </>
          );
        } else {
          content = line;
        }
        return (
          <div key={i} className={visual.row}>
            <span className={visual.surface5}>{i + 1}</span>
            <span className={visual.surface6}>{content}</span>
          </div>
        );
      })}
    </pre>
  </div>
);
