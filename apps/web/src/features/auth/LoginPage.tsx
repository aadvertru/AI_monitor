import { zodResolver } from "@hookform/resolvers/zod";
import { LogIn } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import { ApiError } from "../../lib/api/client";
import { AuthLayout } from "./AuthLayout";
import { useLoginMutation } from "./session";

const schema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

type LoginForm = z.infer<typeof schema>;

type LocationState = {
  from?: { pathname?: string };
  registered?: boolean;
};

export function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const login = useLoginMutation();
  const state = location.state as LocationState | null;
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
    <AuthLayout title="Sign in" subtitle="Open your audit workspace">
      {state?.registered ? (
        <div className="mb-4 rounded-md border border-brand-100 bg-brand-50 px-3 py-2 text-sm text-brand-700">
          Account created. Sign in to continue.
        </div>
      ) : null}
      <form className="space-y-4" noValidate onSubmit={onSubmit}>
        <Field htmlFor="login-email" label="Email" error={errors.email?.message}>
          <Input id="login-email" type="email" autoComplete="email" {...register("email")} />
        </Field>
        <Field
          htmlFor="login-password"
          label="Password"
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
              : "Unable to sign in."}
          </p>
        ) : null}
        <Button type="submit" className="w-full" disabled={login.isPending}>
          <LogIn className="size-4" aria-hidden="true" />
          Sign in
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-subtle">
        No account?{" "}
        <Link className="font-medium text-brand-700 hover:underline" to="/register">
          Create one
        </Link>
      </p>
    </AuthLayout>
  );
}
