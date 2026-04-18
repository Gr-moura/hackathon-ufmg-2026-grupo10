import { useState } from 'react';
import './LoginRoleSelector.css';

export type UserRole = 'Lawyer' | 'Bank Administrator';

interface LoginRoleSelectorProps {
    onSelectRole: (role: UserRole) => void;
    initialRole?: UserRole;
}

export const LoginRoleSelector = ({ onSelectRole, initialRole = 'Lawyer' }: LoginRoleSelectorProps) => {
    const [selectedRole, setSelectedRole] = useState<UserRole>(initialRole);

    return (
        <div className="login-screen__role-block">
            <div className="field-label">Identifique seu perfil</div>
            <div className="tabs">
                <button 
                    type="button" 
                    className={`tab ${selectedRole === 'Lawyer' ? 'active' : ''}`} onClick={() => {
                        setSelectedRole('Lawyer');
                        onSelectRole('Lawyer');
                    }
                }>
                    Advogado
                </button>
                <button 
                    type="button" 
                    className={`tab ${selectedRole === 'Bank Administrator' ? 'active' : ''}`} 
                    onClick={() => {
                        setSelectedRole('Bank Administrator');
                        onSelectRole('Bank Administrator');
                    }
                }>
                    Administrador do banco
                </button>
            </div>
        </div>
    )
};
    