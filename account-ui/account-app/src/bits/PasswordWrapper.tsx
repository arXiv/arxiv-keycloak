import React, { useEffect, useReducer, useRef } from "react";
import Box from "@mui/material/Box";
import IconButton from '@mui/material/IconButton';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

export function useIsPasswordRevealed() {
    const [isPasswordRevealed, toggleIsPasswordRevealed] = useReducer(
        (isPasswordRevealed) => !isPasswordRevealed,
        false
    );
    const passwordInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const passwordInputElement = passwordInputRef.current;
        if (passwordInputElement) {
            const type = isPasswordRevealed ? "text" : "password";
            passwordInputElement.type = type;

            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.attributeName !== "type") {
                        return;
                    }
                    if (passwordInputElement.type === type) {
                        return;
                    }
                    passwordInputElement.type = type;
                });
            });

            observer.observe(passwordInputElement, { attributes: true });

            return () => {
                observer.disconnect();
            };
        }
    }, [isPasswordRevealed]);

    return { isPasswordRevealed, toggleIsPasswordRevealed, passwordInputRef };
}

const PasswordWrapper: React.FC<{ children: JSX.Element }> = ({ children }) => {
    const { isPasswordRevealed, toggleIsPasswordRevealed, passwordInputRef } = useIsPasswordRevealed();

    return (
        <Box display="flex" alignItems="center">
            {React.cloneElement(children, { inputRef: passwordInputRef })}
            <IconButton
                onClick={toggleIsPasswordRevealed}
                aria-label={isPasswordRevealed ? "hide password" : "show password"}
                aria-controls={passwordInputRef.current?.id}
            >
                {isPasswordRevealed ? <VisibilityOff /> : <Visibility />}
            </IconButton>
        </Box>
    );
};

export default PasswordWrapper;
