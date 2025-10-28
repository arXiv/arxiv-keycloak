import { RuntimeProps } from "../RuntimeContext.tsx";
import {ACCOUNT_PASSWORD_VALIDATE_URL} from "../types/aaa-url.ts";
import * as sha1Module from 'js-sha1';

export const PASSWORD_MIN_LENGTH = 15;

function sha1Hash(text: string): string {
    return sha1Module.sha1(text);
}

export async function passwordValidator(password: string, runtimeProps: RuntimeProps): Promise<{valid: boolean, reason?: string | null}> {
    console.log("Validating password", JSON.stringify(password));
    if (password.length < PASSWORD_MIN_LENGTH) {
        return {valid: false, reason: `Password length is ${password.length}, must be at least ${PASSWORD_MIN_LENGTH} characters long`};
    }

    const passwordHash = sha1Hash(password);
    const validationEndpoint = runtimeProps.aaaFetcher.path(ACCOUNT_PASSWORD_VALIDATE_URL).method('post').create();
    const response = await validationEndpoint({length: password.length, password_sha1: passwordHash});
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
