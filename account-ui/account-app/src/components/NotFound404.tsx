import React, {useContext} from 'react';
import { Link } from 'react-router-dom';
import {RuntimeContext} from "../RuntimeContext.tsx";

const NotFound404: React.FC = () => {
    const rutimeProps = useContext(RuntimeContext);

    return (
        <div style={{ textAlign: 'center', padding: '50px', color: '#808080' }}>
            <h1>404 - Page Not Found</h1>
            <p>The page you are looking for does not exist.</p>
            <p>
            <a href={rutimeProps.URLS.arXiv}>Go to arXiv</a>
            </p>
            <p>
            <Link to="/user-account">Go to User Account</Link>
            </p>
        </div>
    );
};

export default NotFound404;
