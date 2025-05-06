/*
WIP
 */

import {
    Container,
    Typography,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableRow,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
} from '@mui/material';
import {LooksOne, LooksTwo} from '@mui/icons-material';

// Define all TeX characters data for the tables
const texCharactersData = [
    // Table 1
    [
        {char: 'Ä', tex: '\\"A'}, {char: 'ä', tex: '\\"a'}, {char: 'Á', tex: "\\'A"},
        {char: 'á', tex: "\\'a"}, {char: 'Ȧ', tex: '\\.A'}, {char: 'ȧ', tex: '\\.a'},
        {char: 'Ā', tex: '\\=A'}
    ],
    // Table 2
    [
        {char: 'ā', tex: '\\=a'}, {char: 'Â', tex: '\\^A'}, {char: 'â', tex: '\\^a'},
        {char: 'À', tex: '\\`A'}, {char: 'à', tex: '\\`a'}, {char: 'Ą', tex: '\\k{A}'},
        {char: 'ą', tex: '\\k{a}'}
    ],
    // ... continuing with all other rows from the original tables
    [
        {char: 'Å', tex: '\\r{A}'}, {char: 'å', tex: '\\r{a}'}, {char: 'Ă', tex: '\\u{A}'},
        {char: 'ă', tex: '\\u{a}'}, {char: 'Ǎ', tex: '\\v{A}'}, {char: 'ǎ', tex: '\\v{a}'},
        {char: 'Ã', tex: '\\~A'}
    ],
    [
        {char: 'ã', tex: '\\~a'}, {char: 'Ć', tex: "\\'C"}, {char: 'ć', tex: "\\'c"},
        {char: 'Ċ', tex: '\\.C'}, {char: 'ċ', tex: '\\.c'}, {char: 'Ĉ', tex: '\\^C'},
        {char: 'ĉ', tex: '\\^c'}
    ],
    [
        {char: 'Ç', tex: '\\c{C}'}, {char: 'ç', tex: '\\c{c}'}, {char: 'Č', tex: '\\v{C}'},
        {char: 'č', tex: '\\v{c}'}, {char: 'Ď', tex: '\\v{D}'}, {char: 'ď', tex: '\\v{d}'},
        {char: 'Ë', tex: '\\"E'}
    ],
    // Continue with remaining rows...
    // I'll include just a selection for brevity in this example
    [
        {char: 'ë', tex: '\\"e'}, {char: 'É', tex: "\\'E"}, {char: 'é', tex: "\\'e"},
        {char: 'Ė', tex: '\\.E'}, {char: 'ė', tex: '\\.e'}, {char: 'Ē', tex: '\\=E'},
        {char: 'ē', tex: '\\=e'}
    ],
];

// TeX Commands data
const texCommandsData = [
    [
        {char: 'å', tex: '{\\aa}'}, {char: 'Å', tex: '{\\AA}'}, {char: 'æ', tex: '{\\ae}'},
        {char: 'Æ', tex: '{\\AE}'}, {char: 'Ð', tex: '{\\DH}'}, {char: 'ð', tex: '{\\dh}'},
        {char: 'đ', tex: '{\\dj}'}
    ],
    [
        {char: 'Đ', tex: '{\\DJ}'}, {char: 'ð', tex: '{\\eth}'}, {char: 'Ð', tex: '{\\ETH}'},
        {char: 'ı', tex: '{\\i}'}, {char: 'ł', tex: '{\\l}'}, {char: 'Ł', tex: '{\\L}'},
        {char: 'ŋ', tex: '{\\ng}'}
    ],
    [
        {char: 'Ŋ', tex: '{\\NG}'}, {char: 'Ø', tex: '{\\O}'}, {char: 'ø', tex: '{\\o}'},
        {char: 'œ', tex: '{\\oe}'}, {char: 'Œ', tex: '{\\OE}'}, {char: 'ß', tex: '{\\ss}'},
        {char: 'þ', tex: '{\\th}'}
    ],
    [
        {char: 'Þ', tex: '{\\TH}'}
    ]
];

export default function AccentedCharactersGuide() {

    return (
        <Container maxWidth="md" sx={{mt: 2, mb: 2}}>
            <Typography variant="h4" component="h1" gutterBottom>
                Entering Accented Characters
            </Typography>

            <Paper elevation={1} sx={{p: 2, mb: 2}}>
                <Typography variant="body1" paragraph>
                    Two methods are supported for entering accented characters into arXiv user records.
                </Typography>

                <List>
                    <ListItem>
                        <ListItemIcon>
                            <LooksOne/>
                        </ListItemIcon>
                        <ListItemText
                            primary="If your browser supports ISO Latin 1 or UTF8/Unicode and you have the appropriate input method enabled on your computer, you can type them directly."
                        />
                    </ListItem>

                    <ListItem>
                        <ListItemIcon>
                            <LooksTwo/>
                        </ListItemIcon>
                        <ListItemText
                            primary="You can also enter accented characters using a subset of TeX syntax. arXiv's subset of TeX supports many of the ways accented characters can be written in TeX, however, it accepts only characters from ISO Latin 1 (which is a subset of Unicode that can be represented as a single byte in UTF-8)."
                        />
                    </ListItem>
                </List>
            </Paper>

            {/* TeX Characters Section */}
            <Typography variant="h5" component="h2" gutterBottom sx={{mt: 4, fontWeight: 'bold'}}>
                TeX Characters:
            </Typography>

            <Paper elevation={1} sx={{p: 3, mb: 4}}>
                <Typography variant="body1" paragraph>
                    The following TeX characters can be embedded anywhere in a word and behave like single characters
                    for purposes of spacing.
                </Typography>

                <Typography variant="h6" gutterBottom>Examples:</Typography>
                <List dense>
                    <ListItem>
                        <ListItemText>
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                Schr\"odinger
                            </Typography>
                            {' -> '}
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                Schrödinger
                            </Typography>
                        </ListItemText>
                    </ListItem>

                    <ListItem>
                        <ListItemText>
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                Universit\'e Paris
                            </Typography>
                            {' -> '}
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                Université Paris
                            </Typography>
                        </ListItemText>
                    </ListItem>
                </List>

                {/* TeX Characters Tables */}
                {texCharactersData.map((row, rowIndex) => (
                    <TableContainer component={Paper} key={`tex-chars-table-${rowIndex}`}
                                    sx={{mt: 1, bgcolor: '#f5f5f5'}}>
                        <Table size="small">
                            <TableBody>
                                    {row.map((item, cellIndex) => (
                                        <TableRow>

                                        <TableCell key={`tex-char-char-${rowIndex}-${cellIndex}`}
                                                   sx={{
                                                       border: "3",
                                                       borderWidth: "3",
                                                       width: "2em"
                                        }}>
                                            <Typography variant="body1" component="span"
                                                        sx={
                                                {
                                                    fontWeight: "bold",
                                                }
                                            }>
                                                {item.char}
                                            </Typography>
                                        </TableCell>
                                            <TableCell key={`tex-char-tex-${rowIndex}-${cellIndex}`} sx={{border: '1', width: "4em"}}>
                                                <Typography variant="body1" component="span">
                                                    {item.tex}
                                                </Typography>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                ))}
            </Paper>

            {/* TeX Commands Section */}
            <Typography variant="h5" component="h2" gutterBottom sx={{mt: 4, fontWeight: 'bold'}}>
                TeX Commands:
            </Typography>

            <Paper elevation={1} sx={{p: 3, mb: 4}}>
                <Typography variant="body1" paragraph>
                    The following commands contain a word which must be terminated with a space or.
                </Typography>

                <Typography variant="h6" gutterBottom>Examples:</Typography>
                <List dense>
                    <ListItem>
                        <ListItemText>
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                M\o ller
                            </Typography>
                            {' -> '}
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                Møller
                            </Typography>
                        </ListItemText>
                    </ListItem>

                    <ListItem>
                        <ListItemText>
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                {"M{\o}ller"}
                            </Typography>
                            {' -> '}
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                Møller
                            </Typography>
                        </ListItemText>
                    </ListItem>

                    <ListItem>
                        <ListItemText>
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                {"M\oller"}
                            </Typography>
                            {' is invalid ('}
                            <Typography variant="body1" component="span" sx={{fontStyle: 'italic'}}>
                                {"\oller"}
                            </Typography>
                            {' is not a valid TeX command)'}
                        </ListItemText>
                    </ListItem>
                </List>

                {/* TeX Commands Tables */}
                {texCommandsData.map((row, rowIndex) => (
                    <TableContainer component={Paper} key={`tex-cmds-table-${rowIndex}`}
                                    sx={{mt: 2, bgcolor: '#f5f5f5'}}>
                        <Table size="small">
                            <TableBody>
                                <TableRow>
                                    {row.map((item, cellIndex) => (
                                        <>
                                        <TableCell key={`tex-cmd-char-${rowIndex}-${cellIndex}`} sx={{bgcolor: '#d0d0d0'}}>
                                            <Typography variant="body1" component="span"   sx={{fontWeight: 'bold', mr: 2}}>
                                                {item.char}
                                            </Typography>
                                        </TableCell>
                                        <TableCell key={`tex-cmd-tex-${rowIndex}-${cellIndex}`} sx={{bgcolor: '#d0d0d0'}}>
                                        <Typography variant="body1" component="span"
                                                sx={{fontWeight: 'bold', mr: 2}}>
                                            {item.tex}
                                        </Typography>
                                       </TableCell>
                                        </>
                                    ))}
                                </TableRow>
                            </TableBody>
                        </Table>
                    </TableContainer>
                ))}
            </Paper>
        </Container>
    );
}