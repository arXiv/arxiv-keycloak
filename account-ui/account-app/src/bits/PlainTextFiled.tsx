import React from 'react';
import TextField, { TextFieldProps } from '@mui/material/TextField';
import { styled } from '@mui/material/styles';

const StyledTextField = styled(TextField)({
    '& .MuiInputLabel-root': {
        position: 'static',
        transform: 'none',
        fontSize: '1em',
        color: 'black',
        fontWeight: 'bold',
        paddingBottom: '6px',
    },
});

const PlainTextField: React.FC<TextFieldProps> = (props) => {
    return (
        <StyledTextField
            {...props}
            slotProps={{
                ...props.slotProps,
                inputLabel: {
                    shrink: true,
                    ...props.slotProps?.inputLabel,
                },
                input: {
                    notched: false,
                    ...props.slotProps?.input,
                },
            }}
        />
    );
};

export default PlainTextField;
