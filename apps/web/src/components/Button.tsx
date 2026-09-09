import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cx } from "./cx";
import { Icon, type IconName } from "./Icon";

/**
 * 按钮：禁用必须带原因（disabledReason → title + aria-disabled），
 * 不允许"静默灰掉"。视觉走全局 .btn 类（base.css）。
 */
export interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "disabled"> {
  variant?: "default" | "primary" | "danger" | "ghost";
  size?: "sm" | "md";
  icon?: IconName | undefined;
  disabled?: boolean;
  disabledReason?: string | undefined;
  children?: ReactNode;
}

export function Button({
  variant = "default",
  size = "md",
  icon,
  disabledReason,
  disabled,
  className,
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  const isDisabled = disabled === true || disabledReason !== undefined;
  return (
    <button
      type={type}
      className={cx(
        "btn",
        variant === "primary" && "primary",
        variant === "danger" && "danger",
        variant === "ghost" && "ghost",
        size === "sm" && "sm",
        className,
      )}
      disabled={disabled}
      aria-disabled={isDisabled && disabled === undefined ? true : undefined}
      title={disabledReason ?? rest.title}
      {...rest}
    >
      {icon !== undefined && <Icon name={icon} size={size === "sm" ? 10 : 11} />}
      {children}
    </button>
  );
}
