
import { createTheme } from '@mui/material/styles';

const arxivTheme = createTheme({
    typography: {
        fontFamily: '"Open Sans", "Lucida Grande", "Helvetica Neue", Helvetica, Arial, sans-serif',
        h1: {
            fontSize: '2em',
            fontWeight: 600,
            lineHeight: 1.125,
            marginBottom: '0.5em',
        },
        h2: {
            fontSize: '1.75em',
            fontWeight: 600,
            lineHeight: 1.125,
            marginBottom: '0.5714em',
        },
        h3: {
            fontSize: '1.5em',
            fontWeight: 600,
            lineHeight: 1.125,
            marginBottom: '0.6666em',
        },
        h4: {
            fontSize: '1.25em',
            fontWeight: 600,
            lineHeight: 1.125,
            marginBottom: '0.8em',
        },
        h5: {
            fontSize: '1.125em',
            fontWeight: 600,
            lineHeight: 1.125,
            marginBottom: '0.8888em',
        },
        h6: {
            fontSize: '1em',
            fontWeight: 600,
            lineHeight: 1.125,
            marginBottom: '1em',
            color: "#2d2d2d",
        },
    },
    components: {
        MuiTextField: {
            defaultProps: {
                variant: 'standard',
                slotProps: {
                    inputLabel: {
                        shrink: true
                    }
                },
            },
        },
        MuiInputLabel: {
            styleOverrides: {
                root: {
                    position: 'static',
                    transform: 'none',
                    fontSize: '1em',
                    color: 'black',
                    padding: '0px',
                    fontWeight: 'bold',
                },
            },
        },
        MuiInput: {
            styleOverrides: {
                root: {
                    border: '1px solid rgba(0, 0, 0, 0.23)',
                    borderRadius: '4px',
                    padding: '6px 8px',
                    marginTop: '6px',
                    backgroundColor: 'white',
                    transition: 'border-color 0.2s',
                    '&:hover': {
                        borderColor: 'rgba(0, 0, 0, 0.87)',
                        boxShadow: '0 0 0 2px rgba(0, 0, 0, 0.1)',
                    },
                    '&.Mui-focused': {
                        borderColor: '#1976d2',
                        borderWidth: '1px',
                    },
                    '&.MuiInput-root': {
                        '&:not(:first-child)': {
                            marginTop: '6px', // or whatever spacing you want
                        },
                    },
                },
                input: {
                    padding: 0,
                },
                underline: {
                    '&:before': {
                        borderBottom: 'none !important',
                    },
                    '&:after': {
                        borderBottom: 'none !important',
                    },
                },
            },
        },
    },
});


export default arxivTheme;
