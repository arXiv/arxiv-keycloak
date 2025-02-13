import React from 'react';
import { Link } from 'react-router-dom';

const NotFound404: React.FC = () => {
    return (
        <div style={{ textAlign: 'center', padding: '50px', color: '#808080' }}>
            <h1>404 - Page Not Found</h1>
            <p>The page you are looking for does not exist.</p>
            <Link to="/">Go Home</Link>
        </div>
    );
};

export default NotFound404;
