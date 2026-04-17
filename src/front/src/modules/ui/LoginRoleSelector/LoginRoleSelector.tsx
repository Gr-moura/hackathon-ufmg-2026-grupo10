import { useState } from 'react';

interface LoginRoleSelectorProps {
    onSelectRole: (role: string) => void;
}

export const LoginRoleSelector = ({ onSelectRole }: LoginRoleSelectorProps) => {
    const [selectedRole, setSelectedRole] = useState('Lawyer');

    return (
        <div className="login-screen__role-block">
            <div className="field-label">Identify Your Role</div>
            <div className="tabs">
                <button 
                    type="button" 
                    className={`tab ${selectedRole === 'Lawyer' ? 'active' : ''}`} onClick={() => {
                        setSelectedRole('Lawyer');
                        onSelectRole('Lawyer');
                    }
                }>
                    Lawyer
                </button>
                <button 
                    type="button" 
                    className={`tab ${selectedRole === 'Bank Administrator' ? 'active' : ''}`} 
                    onClick={() => {
                        setSelectedRole('Bank Administrator');
                        onSelectRole('Bank Administrator');
                    }
                }>
                    Bank Administrator
                </button>
            </div>
        </div>
    )
};
    