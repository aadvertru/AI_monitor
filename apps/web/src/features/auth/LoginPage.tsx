import { zodResolver } from "@hookform/resolvers/zod";
import { LogIn } from "lucide-react";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import { API_BASE_URL, ApiError } from "../../lib/api/client";
import { AuthLayout } from "./AuthLayout";
import { useLoginMutation } from "./session";

type LoginForm = {
  email: string;
  password: string;
};

type LocationState = {
  from?: { pathname?: string };
  registered?: boolean;
};

export function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const login = useLoginMutation();
  const { t } = useTranslation("auth");
  const state = location.state as LocationState | null;
  const schema = useMemo(
    () =>
      z.object({
        email: z.string().email(t("errors.email")),
        password: z.string().min(1, t("errors.passwordLogin")),
      }),
    [t],
  );
  const {
    formState: { errors },
    handleSubmit,
    register,
  } = useForm<LoginForm>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = handleSubmit((values) => {
    login.mutate(values, {
      onSuccess: () => {
        navigate(state?.from?.pathname || "/audits", { replace: true });
      },
    });
  });

  return (
    <AuthLayout title={t("signIn")} subtitle={t("openWorkspace")}>
      {state?.registered ? (
        <div className="mb-4 rounded-md border border-brand-100 bg-brand-50 px-3 py-2 text-sm text-brand-700">
          {t("accountCreated")}
        </div>
      ) : null}
      <form className="space-y-4" noValidate onSubmit={onSubmit}>
        <Field htmlFor="login-email" label={t("email")} error={errors.email?.message}>
          <Input id="login-email" type="email" autoComplete="email" {...register("email")} />
        </Field>
        <Field
          htmlFor="login-password"
          label={t("password")}
          error={errors.password?.message}
        >
          <Input
            id="login-password"
            type="password"
            autoComplete="current-password"
            {...register("password")}
          />
        </Field>
        {login.error ? (
          <p className="text-sm text-red-700">
            {login.error instanceof ApiError
              ? login.error.message
              : t("errors.signIn")}
          </p>
        ) : null}
        {import.meta.env.DEV && login.error && !(login.error instanceof ApiError) ? (
          <p className="break-all rounded-md border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-800">
            {t("debug", {
              message: login.error instanceof Error
                ? `${login.error.name}: ${login.error.message}`
                : String(login.error),
            })}
          </p>
        ) : null}
        <Button type="submit" className="w-full" disabled={login.isPending}>
          <LogIn className="size-4" aria-hidden="true" />
          {t("signIn")}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-subtle">
        {t("noAccount")}{" "}
        <Link className="font-medium text-brand-700 hover:underline" to="/register">
          {t("createOne")}
        </Link>
      </p>
      {import.meta.env.DEV ? (
        <p className="mt-3 break-all text-center text-xs text-subtle">
          {t("apiDebug", { url: API_BASE_URL })}
        </p>
      ) : null}
    </AuthLayout>
  );
}
