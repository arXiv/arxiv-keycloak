import { RuntimeProps } from "../RuntimeContext.tsx";
import {ACCOUNT_PASSWORD_VALIDATE_URL} from "../types/aaa-url.ts";

export const PASSWORD_MIN_LENGTH = 15;

export async function passwordValidator(password: string, runtimeProps: RuntimeProps): Promise<{valid: boolean, reason?: string | null}> {
    if (password.length < PASSWORD_MIN_LENGTH) {
        return {valid: false, reason: `Password must be at least ${PASSWORD_MIN_LENGTH} characters long`};
    }

    const validationEndpoint = runtimeProps.aaaFetcher.path(ACCOUNT_PASSWORD_VALIDATE_URL).method('post').create();
    const response = await validationEndpoint({password});
    return response.data;
}


export function emailValidator(email: string): boolean {
    // Regular expression for validating an email address
    const emailPattern = /^[\w.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    return emailPattern.test(email);
}

export function endorsementCodeValidator(code: string): boolean {
    return code.length == 6;
}
