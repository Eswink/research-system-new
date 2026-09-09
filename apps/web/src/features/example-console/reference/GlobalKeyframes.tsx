/** Reference: components/atoms.jsx; EXAMPLE ONLY. */
export const GlobalKeyframes = () => (
  <style>
    {[
      "\n    @keyframes spin { to { transform: rotate(360deg); } }\n    ",
      "@keyframes pulse {\n      0%   { transform: scale(0.6); opacity: 0.6; }\n  ",
      "    100% { transform: scale(1.8); opacity: 0; }\n    }\n    @keyframes ",
      "fadeIn { from { opacity: 0; transform: translateY(2px); } to { opacity: ",
      "1; transform: none; } }\n    @keyframes stream-in {\n      from { opacity: ",
      "0; transform: translateX(-4px); background: var(--accent-dim); }\n      ",
      "to { opacity: 1; transform: none; }\n    }\n  ",
    ].join("")}
  </style>
);
