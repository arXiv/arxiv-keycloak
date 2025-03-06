import React, { useState, useContext } from "react";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";
import { RuntimeContext} from "../RuntimeContext";
import Tooltip from "@mui/material/Tooltip";
import Link from "@mui/material/Link";
import LinkIcon from "@mui/icons-material/Link";

const MathJaxToggle: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const mathjaxCookieName = runtimeProps.MATHJAX_COOKIE_NAME;

    // Function to get the MathJax cookie value
    const getMathjaxCookie = () => {
        const cookies = document.cookie.split("; ").reduce((acc, cookie) => {
            const [name, value] = cookie.split("=");
            acc[name] = value;
            return acc;
        }, {} as Record<string, string>);
        return cookies[mathjaxCookieName] || "disabled";
    };

    // Function to set the MathJax cookie and reload the page
    const setMathjaxCookie = () => {
        const newValue = mathjaxEnabled ? "disabled" : "enabled";
        const expireDate = new Date();
        expireDate.setFullYear(expireDate.getFullYear() + 1); // Expires in 1 year

        document.cookie = `${mathjaxCookieName}=${newValue}; domain=.arxiv.org; path=/; expires=${expireDate.toUTCString()}`;
        window.location.reload(); // Reload page to apply the changes
    };

    // State to manage the toggle switch
    const [mathjaxEnabled, setMathjaxEnabled] = useState(getMathjaxCookie() === "enabled");

    // Handle the toggle switch change
    const handleToggle = () => {
        setMathjaxEnabled((prev) => !prev);
        setMathjaxCookie();
    };
    // const _foo = ();

    return (
        <span>
            <Tooltip
                slotProps={{tooltip: {sx: {fontSize: "1em"}} }}
                title="MathJax is a javascript display engine for rendering TEX or MathML-coded mathematics in browsers without requiring font installation or browser plug-ins. Any modern browser with javascript enabled will be MathJax-ready. For general information about MathJax, visit mathjax.org."
            >
                <FormControlLabel
                    control={<Switch checked={mathjaxEnabled} onChange={handleToggle} disabled={user === null}/>}
                    label="Use MathJax" />
            </Tooltip>
            <Link href={runtimeProps.URLS.mathJaxHelp} target="_blank"><LinkIcon/>Help</Link>
        </span>
    );
}

export default MathJaxToggle;
