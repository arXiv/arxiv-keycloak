import React from 'react';
import TextField, { TextFieldProps } from '@mui/material/TextField';
import { styled } from '@mui/material/styles';

const StyledTextField = styled(TextField)({
    '& .MuiInputLabel-root': {
        position: 'static',
        transform: 'none',
        fontSize: '1em',
        color: 'black',
        padding: '0px 0px',
        fontWeight: 'bold',
    },
    '& .MuiInputBase-root': {
        border: '1px solid rgba(0, 0, 0, 0.23)',
        borderRadius: '4px',
        padding: '6px 8px',
        transition: 'border-color 0.2s',
        marginTop: '6px',
        backgroundColor: 'white',
    },
    '& .MuiInputBase-root:hover': {
        borderColor: 'rgba(0, 0, 0, 0.87)',
        boxShadow: '0 0 0 2px rgba(0, 0, 0, 0.1)',
    },
    '& .MuiInputBase-root.Mui-focused': {
        borderColor: '#1976d2',
        borderWidth: '1px',
    },
    '& .MuiInputBase-input': {
        padding: 0,
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
                    ...props.slotProps?.input,
                    notched: false,
                    disableUnderline: true,
                },
            }}
        />
    );
};

export default PlainTextField;
