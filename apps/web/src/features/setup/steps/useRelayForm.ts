import { useState } from "react";

import type { LlmEndpointCreateDto } from "../../../api/types";

export interface RelayFormState {
  name: string;
  setName: (value: string) => void;
  baseUrl: string;
  setBaseUrl: (value: string) => void;
  apiStyle: string;
  setApiStyle: (value: string) => void;
  apiKey: string;
  setApiKey: (value: string) => void;
  submit: () => void;
}

/** Relay 表单 draft state（transient；不持久化，刷新即失） */
export function useRelayForm(onSubmit: (payload: LlmEndpointCreateDto) => void): RelayFormState {
  const [name, setName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiStyle, setApiStyle] = useState<string>("chat_completions");
  const [apiKey, setApiKey] = useState("");

  const submit = () => {
    const payload: LlmEndpointCreateDto = {
      name: name || "my-relay",
      base_url: baseUrl,
      protocol: "OPENAI_COMPATIBLE",
      api_style: apiStyle as "chat_completions" | "responses",
    };
    if (apiKey.length > 0) {
      payload.api_key = apiKey;
    }
    onSubmit(payload);
  };

  return { name, setName, baseUrl, setBaseUrl, apiStyle, setApiStyle, apiKey, setApiKey, submit };
}
