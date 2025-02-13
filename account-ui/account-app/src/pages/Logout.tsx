import {useContext, useEffect} from "react";
import {RuntimeContext} from "../RuntimeContext.tsx";

const Logout = () => {
    const runtimeContext = useContext(RuntimeContext);
    useEffect(() => {
        window.location.href = runtimeContext.AAA_URL + "/logout?next_page=/";
    }, []);

    return <h2>Redirecting...</h2>;
};

export default Logout;
