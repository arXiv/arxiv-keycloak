import { useNavigate } from 'react-router-dom';
import { ReactNode, CSSProperties } from 'react';

interface NavigateLinkProps {
    to: string;
    children: ReactNode;
    color?: string;
    style?: CSSProperties;
}

const NavigateLink = ({
                          to,
                          children,
                          color = 'primary',
                          style = {}
                      }: NavigateLinkProps): JSX.Element => {
    const navigate = useNavigate();

    return (
        <span
            onClick={() => navigate(to)}
            style={{
                color: color,
                textDecoration: 'underline',
                cursor: 'pointer',
                ...style
            }}
        >
      {children}
    </span>
    );
};

export default NavigateLink;