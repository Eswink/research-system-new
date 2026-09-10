/** 通知投影客户端（WP-G；outbox 事件白名单投影 + 已读标记）。 */

import { newIdempotencyKey, request } from "./http";
import type { NotificationsViewDto } from "./types";

export const notificationsClient = {
  list(limit = 50): Promise<NotificationsViewDto> {
    return request(`/notifications?limit=${String(limit)}`, { method: "GET" });
  },
  markRead(eventId: string): Promise<void> {
    return request(
      `/notifications/${encodeURIComponent(eventId)}/read`,
      { method: "POST" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
