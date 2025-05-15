
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
});


export default arxivTheme;
