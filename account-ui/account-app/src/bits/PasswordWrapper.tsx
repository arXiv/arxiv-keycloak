import React from "react";
import Box from "@mui/material/Box";
import IconButton from '@mui/material/IconButton';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import { useEffect, useReducer } from "react";


export function useIsPasswordRevealed(params: {passwordInputId: string;})
{
    const { passwordInputId } = params;
    const [isPasswordRevealed, toggleIsPasswordRevealed] = useReducer((isPasswordRevealed) => !isPasswordRevealed, false);
    useEffect(() => {
        const passwordInputElement = document.getElementById(passwordInputId);
        if (passwordInputElement && passwordInputElement instanceof HTMLInputElement ) {
            const type = isPasswordRevealed ? "text" : "password";
            passwordInputElement.type = type;
            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
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
    return { isPasswordRevealed, toggleIsPasswordRevealed };
}
//# sourceMappingURL=useIsPasswordRevealed.js.map


const PasswordWrapper: React.FC<{passwordInputId: string, children: JSX.Element}> = ({passwordInputId, children}) => {
    const { isPasswordRevealed, toggleIsPasswordRevealed } = useIsPasswordRevealed({ passwordInputId });

    return (
        <Box display="flex" alignItems="center">
            {children}
            <IconButton
                onClick={toggleIsPasswordRevealed}
                aria-label={isPasswordRevealed ? "hide password" : "show password"}
                aria-controls={passwordInputId}
            >
                {isPasswordRevealed ? <VisibilityOff /> : <Visibility />}
            </IconButton>
        </Box>
    );
};

export default PasswordWrapper;
