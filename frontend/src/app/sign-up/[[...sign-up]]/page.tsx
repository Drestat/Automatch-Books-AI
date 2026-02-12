import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
    return (
        <div className="flex justify-center items-center py-24 min-h-screen bg-black">
            <SignUp
                path="/sign-up"
                routing="path"
                signInUrl="/sign-in"
                forceRedirectUrl="/dashboard"
            />
        </div>
    );
}
