import { zodResolver } from "@hookform/resolvers/zod";
import { UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import { ApiError } from "../../lib/api/client";
import { AuthLayout } from "./AuthLayout";
import { useRegisterMutation } from "./session";

const schema = z
  .object({
    email: z.string().email("Enter a valid email address."),
    password: z.string().min(1, "Enter a password."),
    confirmPassword: z.string().min(1, "Confirm your password."),
  })
  .refine((value) => value.password === value.confirmPassword, {
    message: "Passwords must match.",
    path: ["confirmPassword"],
  });

type RegisterForm = z.infer<typeof schema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const registerAccount = useRegisterMutation();
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
    <AuthLayout title="Create account" subtitle="Start with an owned audit space">
      <form className="space-y-4" noValidate onSubmit={onSubmit}>
        <Field htmlFor="register-email" label="Email" error={errors.email?.message}>
          <Input
            id="register-email"
            type="email"
            autoComplete="email"
            {...register("email")}
          />
        </Field>
        <Field
          htmlFor="register-password"
          label="Password"
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
          label="Confirm password"
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
              : "Unable to create account."}
          </p>
        ) : null}
        <Button type="submit" className="w-full" disabled={registerAccount.isPending}>
          <UserPlus className="size-4" aria-hidden="true" />
          Create account
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-subtle">
        Already registered?{" "}
        <Link className="font-medium text-brand-700 hover:underline" to="/login">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
