import { zodResolver } from "@hookform/resolvers/zod";
import { UserPlus } from "lucide-react";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import { ApiError } from "../../lib/api/client";
import { AuthLayout } from "./AuthLayout";
import { useRegisterMutation } from "./session";

type RegisterForm = {
  email: string;
  password: string;
  confirmPassword: string;
};

export function RegisterPage() {
  const navigate = useNavigate();
  const registerAccount = useRegisterMutation();
  const { t } = useTranslation("auth");
  const schema = useMemo(
    () =>
      z
        .object({
          email: z.string().email(t("errors.email")),
          password: z.string().min(1, t("errors.passwordRegister")),
          confirmPassword: z.string().min(1, t("errors.confirmPassword")),
        })
        .refine((value) => value.password === value.confirmPassword, {
          message: t("errors.passwordsMatch"),
          path: ["confirmPassword"],
        }),
    [t],
  );
  const {
    formState: { errors },
    handleSubmit,
    register,
  } = useForm<RegisterForm>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", confirmPassword: "" },
  });

  const onSubmit = handleSubmit((values) => {
    registerAccount.mutate(
      { email: values.email, password: values.password },
      {
        onSuccess: () => {
          navigate("/login", { replace: true, state: { registered: true } });
        },
      },
    );
  });

  return (
    <AuthLayout title={t("register")} subtitle={t("startWorkspace")}>
      <form className="space-y-4" noValidate onSubmit={onSubmit}>
        <Field htmlFor="register-email" label={t("email")} error={errors.email?.message}>
          <Input
            id="register-email"
            type="email"
            autoComplete="email"
            {...register("email")}
          />
        </Field>
        <Field
          htmlFor="register-password"
          label={t("password")}
          error={errors.password?.message}
        >
          <Input
            id="register-password"
            type="password"
            autoComplete="new-password"
            {...register("password")}
          />
        </Field>
        <Field
          htmlFor="register-confirm-password"
          label={t("confirmPassword")}
          error={errors.confirmPassword?.message}
        >
          <Input
            id="register-confirm-password"
            type="password"
            autoComplete="new-password"
            {...register("confirmPassword")}
          />
        </Field>
        {registerAccount.error ? (
          <p className="text-sm text-red-700">
            {registerAccount.error instanceof ApiError
              ? registerAccount.error.message
              : t("errors.register")}
          </p>
        ) : null}
        <Button type="submit" className="w-full" disabled={registerAccount.isPending}>
          <UserPlus className="size-4" aria-hidden="true" />
          {t("register")}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-subtle">
        {t("alreadyRegistered")}{" "}
        <Link className="font-medium text-brand-700 hover:underline" to="/login">
          {t("signIn")}
        </Link>
      </p>
    </AuthLayout>
  );
}
