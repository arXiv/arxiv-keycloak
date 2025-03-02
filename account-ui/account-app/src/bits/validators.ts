

export function passwordValidator(password: string): boolean {
    // Check length requirement
    if (password.length < 8) {
        return false;
    }

    const allowedPattern = /^[A-Za-z0-9_.+#\-=\/:;(){}\[\]%^]+$/;
    const underscorePattern = /_/;

    if (!allowedPattern.test(password)) {
        return false;
    }

    if (!underscorePattern.test(password)) {
        return false;
    }

    return true;
}


export function emailValidator(email: string): boolean {
    // Regular expression for validating an email address
    const emailPattern = /^[\w.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    return emailPattern.test(email);
}

export function endorsementCodeValidator(code: string): boolean {
    return code.length == 6;
}
